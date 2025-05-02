import os
from pathlib import Path
import pickle
import uuid
import xgboost as xgb
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dropout, Dense
import numpy as np
import pandas as pd
import random
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
import warnings

warnings.filterwarnings('always', category=UserWarning, message=".*compiled the loaded model.*")


class FraudDetector:
    def __init__(self, model_dir="models"):
        self.xgb_model = None
        self.lstm_model = None
        self.scaler = StandardScaler()
        self.feature_cols = []
        self.model_dir = model_dir

        base_dir = Path(__file__).resolve().parent
        self.model_dir = base_dir / model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)


    def preprocess_data(self, df):
        df = df.drop(columns=['transaction_id', 'timestamp'], errors='ignore')
        df = pd.get_dummies(df, columns=['currency', 'location', 'device_type', 'sender_wallet', 'receiver_wallet'], drop_first=True)
        df = df.apply(pd.to_numeric, errors='coerce')

        X = df.drop(columns=['is_fraud'])
        y = df['is_fraud']
        self.feature_cols = X.columns.tolist()

        numerical_cols = ['amount', 'gas_fee', 'is_smart_contract']
        X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])

        smote = SMOTE()
        X_bal, y_bal = smote.fit_resample(X, y)

        return X_bal, y_bal

    def create_lstm_sequences(self, X, y, window_size=10):
        X_seq, y_seq = [], []
        for i in range(len(X) - window_size):
            window = X.iloc[i:i+window_size].values.astype(np.float32)
            label = y.iloc[i + window_size]
            X_seq.append(window)
            y_seq.append(label)
        return np.array(X_seq), np.array(y_seq)

    def build_lstm_model(self, input_shape):
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def save_model(self, version):
        model_folder = os.path.join(self.model_dir, f"FraudDetectorModels_v{version}")
        os.makedirs(model_folder, exist_ok=True)

        xgb_model_path = os.path.join(model_folder, "xgb_model.pkl")
        with open(xgb_model_path, 'wb') as f:
            pickle.dump(self.xgb_model, f)

        lstm_model_path = os.path.join(model_folder, "lstm_model.h5")
        self.lstm_model.save(lstm_model_path)

        scaler_path = os.path.join(model_folder, "scaler.pkl")
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)

    def train(self, df):
        X, y = self.preprocess_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.xgb_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        self.xgb_model.fit(X_train, y_train)
        print("XGBoost Evaluation:")
        print(classification_report(y_test, self.xgb_model.predict(X_test)))

        X_seq_train, y_seq_train = self.create_lstm_sequences(X_train, y_train)
        X_seq_test, y_seq_test = self.create_lstm_sequences(X_test, y_test)

        self.lstm_model = self.build_lstm_model(X_seq_train.shape[1:])
        self.lstm_model.fit(X_seq_train, y_seq_train, epochs=5, batch_size=32, validation_data=(X_seq_test, y_seq_test))

        existing_versions = [f for f in os.listdir(self.model_dir) if f.startswith('FraudDetectorModels_v')]
        version = len(existing_versions) + 1
        self.save_model(version)

    def load_model(self, version):
        model_folder = os.path.join(self.model_dir, f"FraudDetectorModels_v{version}")

        xgb_model_path = os.path.join(model_folder, "xgb_model.pkl")
        with open(xgb_model_path, 'rb') as f:
            self.xgb_model = pickle.load(f)

        lstm_model_path = os.path.join(model_folder, "lstm_model.h5")
        self.lstm_model = load_model(lstm_model_path)

        scaler_path = os.path.join(model_folder, "scaler.pkl")
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)

    def predict(self, new_transaction_dict):
        latest_version = len([f for f in os.listdir(self.model_dir) if f.startswith('FraudDetectorModels_v')])

        self.load_model(latest_version)

        df = pd.DataFrame([new_transaction_dict])
        df = pd.get_dummies(df)

        missing_cols = [col for col in self.feature_cols if col not in df.columns]
        if missing_cols:
            missing_data = pd.DataFrame(0, index=df.index, columns=missing_cols)
            df = pd.concat([df, missing_data], axis=1)

        df = df[self.feature_cols].copy()
        bool_cols = df.select_dtypes(include=['bool']).columns
        df[bool_cols] = df[bool_cols].astype(int)

        numeric_cols = ['amount', 'gas_fee', 'is_smart_contract']
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = df[col].astype(float)

        df[numeric_cols] = self.scaler.transform(df[numeric_cols])

        xgb_pred = self.xgb_model.predict_proba(df)[0][1]

        lstm_input = np.tile(df.values, (10, 1)).reshape((1, 10, df.shape[1]))
        lstm_pred = self.lstm_model.predict(lstm_input, verbose=0)[0][0]

        final_score = (xgb_pred + lstm_pred) / 2
        return 1 if final_score > 0.5 else 0
