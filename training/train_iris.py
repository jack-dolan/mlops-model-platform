#!/usr/bin/env python3
"""Train an Iris classifier and save it."""

import pickle
from pathlib import Path

import mlflow
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


def main():
    # load data
    iris = load_iris()
    X, y = iris.data, iris.target
    feature_names = iris.feature_names
    target_names = iris.target_names

    # train/test split - 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # model params - easy to tweak
    params = {
        "n_estimators": 100,
        "max_depth": 5,
        "random_state": 42,
    }

    # start mlflow run
    mlflow.set_experiment("iris-classifier")

    with mlflow.start_run():
        # log params
        mlflow.log_params(params)

        # train
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)

        # evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Accuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=target_names))

        # log metrics
        mlflow.log_metric("accuracy", accuracy)

        # save model to disk
        model_dir = Path(__file__).parent.parent / "models"
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / "model.pkl"

        model_info = {
            "model": model,
            "feature_names": feature_names,
            "target_names": target_names,
            "version": "1.0.0",
        }

        with open(model_path, "wb") as f:
            pickle.dump(model_info, f)

        print(f"\nModel saved to {model_path}")

        # also log to mlflow
        mlflow.sklearn.log_model(model, "model")


if __name__ == "__main__":
    main()
