import sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT_ROOT/"src"))
from sklearn.metrics import classification_report, confusion_matrix, balanced_accuracy_score
from joblib import load
import pandas as pd
from strokeguard.ai.features import FEATURE_NAMES
df=pd.read_csv(PROJECT_ROOT/"data/generated/strokeguard_windows.csv")
m=load(PROJECT_ROOT/"models/strokeguard_linear.joblib")
pred=m.predict(df[FEATURE_NAMES])
print(classification_report(df.risk_state,pred,zero_division=0))
print("balanced_accuracy:",balanced_accuracy_score(df.risk_state,pred))
print("confusion_matrix:\n",confusion_matrix(df.risk_state,pred,labels=m.classes_))
