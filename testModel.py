import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
# import joblib

CATEGORICAL_FEATURES = ['Gender', 'Personality', 'Preferred_Scent', 'Preferred_Color', 'Price', 'Age']
MODEL_PATH = 'perfume_recommender.pkl'

def load_data(filepath):
    """CSV 파일을 불러와 DataFrame으로 반환"""
    return pd.read_csv(filepath)

def build_pipeline():
    """전처리 및 분류기가 포함된 파이프라인 생성"""
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES)
        ],
        remainder='passthrough'
    )
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    return pipeline

def split_data(df, target_col='Recommend_Perfume_Id', test_size=0.2, random_state=42):
    """학습/테스트 데이터 분할"""
    X = df.drop(target_col, axis=1)
    y = df[target_col]
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

def train_model(pipeline, X_train, y_train):
    """모델 학습"""
    pipeline.fit(X_train, y_train)
    return pipeline

def evaluate_model(pipeline, X_test, y_test):
    """모델 평가"""
    accuracy = pipeline.score(X_test, y_test)
    print(f"Test Accuracy: {accuracy:.2f}")
    return accuracy

# def save_model(pipeline, path=MODEL_PATH):
#     """모델 저장"""
#     joblib.dump(pipeline, path)

# def load_model(path=MODEL_PATH):
#     """저장된 모델 불러오기"""
#     return joblib.load(path)

def predict_perfume(input_data, model_pipeline):
    """입력 데이터에 대한 향수 추천 결과 반환 (출력 X)"""
    try:
        input_df = pd.DataFrame([input_data])
        proba = model_pipeline.predict_proba(input_df)[0]
        return {
            'predicted_id': model_pipeline.predict(input_df)[0],
            'confidence': round(np.max(proba), 2),
            # 'top_3': model_pipeline.classes_[np.argsort(proba)[-3:]][::-1].tolist()
        }
    except Exception as e:
        return {'error': str(e)}

def print_prediction_result(result):
    """예측 결과 출력"""
    if result is None or 'error' in result:
        print(f"예측에 실패했습니다. 오류: {result.get('error', '알 수 없는 오류')}")
    else:
        print(f"""추천 결과:
                - ID: {result['predicted_id']}
                - 신뢰도: {result['confidence']}""")


def find_scent(input_data):
    # 1. 데이터 로드 : excel csv 파일위치 절대주소
    df = load_data('perfume_training_df.csv')

    # 2. 파이프라인 생성
    pipeline = build_pipeline()

    # 3. 데이터 분할
    X_train, X_test, y_train, y_test = split_data(df)

    # 4. 모델 학습
    trained_pipeline = train_model(pipeline, X_train, y_train)

    # 5. 모델 평가
    evaluate_model(trained_pipeline, X_test, y_test)

    # # 6. 모델 저장
    # save_model(trained_pipeline)

    # 7. 샘플 예측 및 결과 출력

    result = predict_perfume(input_data, trained_pipeline)
    print_prediction_result(result)

    return result


def main():
    # 1. 데이터 로드 : excel csv 파일위치 절대주소
    df = load_data('perfume_training_df.csv')

    # 2. 파이프라인 생성
    pipeline = build_pipeline()

    # 3. 데이터 분할
    X_train, X_test, y_train, y_test = split_data(df)

    # 4. 모델 학습
    trained_pipeline = train_model(pipeline, X_train, y_train)

    # 5. 모델 평가
    evaluate_model(trained_pipeline, X_test, y_test)

    # # 6. 모델 저장
    # save_model(trained_pipeline)

    # 7. 샘플 예측 및 결과 출력
    sample_input = {
        'Age': 30,
        'Gender': 'Woman',
        'Personality': 'Agreeableness',
        'Preferred_Scent': 'Floral',
        'Preferred_Color': 'Yellow',
        'Price': 'Entry'
    }
    result = predict_perfume(sample_input, trained_pipeline)
    print_prediction_result(result)

if __name__ == "__main__":
    main()
