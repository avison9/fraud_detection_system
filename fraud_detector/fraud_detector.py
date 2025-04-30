import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report
import xgboost as xgb
import pickle

class FraudDetector:
    def __init__(self, model_type='xgboost'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_cols = []
    
    def preprocess_data(self, df):
        df = df.drop(columns=['transaction_id', 'timestamp'])
        
        df = pd.get_dummies(df, columns=[
            'currency', 'location', 'device_type', 'sender_wallet', 'receiver_wallet'
        ], drop_first=True)

        X = df.drop(columns=['is_fraud'])
        y = df['is_fraud']

        numerical_cols = ['amount', 'gas_fee', 'is_smart_contract']
        X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])
        
        smote = SMOTE()
        X_bal, y_bal = smote.fit_resample(X, y)

        self.feature_cols = X_bal.columns.tolist()
        return X_bal, y_bal

    def train(self, df):
        X, y = self.preprocess_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
            self.model.fit(X_train, y_train)
            self.evaluate(X_test, y_test)

    def evaluate(self, X_test, y_test):
        y_pred = self.model.predict(X_test)
        print(classification_report(y_test, y_pred))

    def predict(self, new_transaction_dict):
      df = pd.DataFrame([new_transaction_dict])
      df = pd.get_dummies(df)

      # Add missing columns (zero-filled)
      missing_cols = [col for col in self.feature_cols if col not in df.columns]
      df_missing = pd.DataFrame(0, index=df.index, columns=missing_cols)
      df = pd.concat([df, df_missing], axis=1)

      # Drop unexpected extra columns
      df = df[[col for col in df.columns if col in self.feature_cols]]

      # Reorder to match model input
      df = df[self.feature_cols]

      # Scale only the numerical columns
      numerical_cols = ['amount', 'gas_fee', 'is_smart_contract']
      df[numerical_cols] = self.scaler.transform(df[numerical_cols])

      # Predict
      prediction = self.model.predict(df)
      return prediction[0]