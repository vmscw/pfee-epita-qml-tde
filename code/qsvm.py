# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.23.3",
#     "matplotlib>=3.11.1",
#     "numpy>=2.5.2",
#     "openpyxl>=3.1.5",
#     "pandas>=3.0.5",
#     "scikit-learn>=1.9.0",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell
def _():
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from scipy.optimize import minimize
    from sklearn.metrics import accuracy_score, confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    return (
        OneHotEncoder,
        StandardScaler,
        accuracy_score,
        confusion_matrix,
        minimize,
        np,
        pd,
        train_test_split,
    )


@app.cell
def _(pd):
    df = pd.read_excel("BEST.xlsx")

    print(f"Shape: {df.shape}")
    # print(df.head())

    df = df.drop(columns=["PARTICIPANT.NUMBER"])

    test_columns = [col for col in df.columns if "TEST" in col]
    df = df.drop(columns=test_columns)

    print(f"Dropped {len(test_columns)} TEST columns")
    print(f"Remaining shape: {df.shape}")
    return (df,)


@app.cell
def _(df):
    target_columns = [
    	"INTERVIEW.MARK.SPANISH",
    	"INTERVIEW.MARK.BASQUE",
    	"INTERVIEW.MARK.ENGLISH",
    ]

    categorical_columns = [
    	"GENDER",
    	"MAXIMUM.EDUCATIONAL.LEVEL",
    	"HANDEDNESS",
    ]

    feature_columns = [col for col in df.columns if col not in target_columns]

    numerical_columns = [col for col in feature_columns if col not in categorical_columns]

    print("Categorical:")
    print(categorical_columns)

    print("\nNumerical:")
    print(numerical_columns)

    print("\nTargets:")
    print(target_columns)
    return categorical_columns, feature_columns, numerical_columns


@app.cell
def _(df):
    missing = df.isna().sum()
    missing = missing[missing > 0]

    if len(missing) == 0:
    	print("No missing values.")
    else:
    	print(missing)
    return


@app.cell
def _(OneHotEncoder, StandardScaler):
    encoder = OneHotEncoder(
    	handle_unknown="ignore",
    	sparse_output=False,
    )

    scaler = StandardScaler()
    return encoder, scaler


@app.cell
def _(
    categorical_columns,
    encoder,
    feature_columns,
    np,
    numerical_columns,
    scaler,
    train_test_split,
):
    def prepare_data(df, target):
    	X = df[feature_columns].copy()
    	# y = df[target].to_numpy(dtype=float)

    	perfect_score = df[target].max()

    	y = np.where(
    		df[target].to_numpy() == perfect_score,
    		1.0,
    		-1.0,
    	)

    	X_train, X_test, y_train, y_test = train_test_split(
    		X,
    		y,
    		test_size=0.2,
    		random_state=42,
    		stratify=y,
    	)

    	encoder.fit(X_train[categorical_columns])

    	X_train_cat = encoder.transform(X_train[categorical_columns])
    	X_test_cat = encoder.transform(X_test[categorical_columns])

    	X_train_num = X_train[numerical_columns].to_numpy(dtype=float)
    	X_test_num = X_test[numerical_columns].to_numpy(dtype=float)

    	X_train = np.hstack([X_train_num, X_train_cat])
    	X_test = np.hstack([X_test_num, X_test_cat])

    	scaler.fit(X_train)

    	X_train = scaler.transform(X_train)
    	X_test = scaler.transform(X_test)

    	return X_train, X_test, y_train, y_test

    return (prepare_data,)


@app.cell
def kernel(np):
    def kernel(x, z, gamma=1.0):
    	diff = x - z
    	return np.exp(-gamma * np.dot(diff, diff))

    return (kernel,)


@app.cell
def train_svr(kernel, minimize, np):
    def train_svm(X_train, y_train, lambda_=1.0, seed=42):
    	"""
    	Returns whatever parameters are necessary for prediction.
    	"""
    	n = len(X_train)

    	K = np.array([[kernel(X_train[i], X_train[j]) for j in range(n)] for i in range(n)])

    	def objective(alpha):
    		return -np.sum(alpha) + 0.25 * np.sum(
    			alpha[:, None] * alpha[None, :] * y_train[:, None] * y_train[None, :] * K
    		)

    	alpha_initial = np.zeros(n)

    	bounds = [(0.0, lambda_) for _ in range(n)]

    	constraints = {
    		"type": "eq",
    		"fun": lambda alpha: np.dot(alpha, y_train),
    	}

    	result = minimize(
    		objective,
    		alpha_initial,
    		method="SLSQP",
    		bounds=bounds,
    		constraints=constraints,
    		options={
    			"maxiter": 1000,
    			"ftol": 1e-8,
    			"disp": True,
    		},
    	)

    	if not result.success:
    		raise RuntimeError(result.message)

    	alpha = result.x

    	print(alpha)

    	free = (alpha > 1e-6) & (alpha < lambda_ - 1e-6)

    	if not np.any(free):
    		raise RuntimeError("No free support vectors found; cannot recover b.")

    	b_values = []

    	for k in np.where(free)[0]:
    		value = y_train[k]

    		for i in range(n):
    			value -= alpha[i] * y_train[i] * kernel(X_train[i], X_train[k])

    		b_values.append(value)

    	b = np.mean(b_values)

    	return alpha, b

    return (train_svm,)


@app.cell
def _(kernel, np):
    def predict_svm(X, X_train, y_train, alpha, b):
    	predictions = []

    	for x in X:
    		prediction = b

    		for i, x_train in enumerate(X_train):
    			prediction += alpha[i] * y_train[i] * kernel(x_train, x)

    		predictions.append(prediction)

    	return np.array(predictions)

    return (predict_svm,)


@app.cell
def _(df, np, prepare_data):
    target = "INTERVIEW.MARK.ENGLISH"

    X_train, X_test, y_train, y_test = prepare_data(df, target)

    print("X_train:", X_train.shape)
    print("X_test:", X_test.shape)
    print("y_train:", y_train.shape)
    print("y_test:", y_test.shape)

    print(np.unique(y_train, return_counts=True))
    return X_test, X_train, y_test, y_train


@app.cell
def _(X_train, train_svm, y_train):
    alpha, b = train_svm(
    	X_train,
    	y_train,
    )
    return alpha, b


@app.cell
def _(
    X_test,
    X_train,
    accuracy_score,
    alpha,
    b,
    confusion_matrix,
    np,
    predict_svm,
    y_test,
    y_train,
):
    y_pred = predict_svm(
        X_test,
        X_train,
        y_train,
        alpha,
        b,
    )
    y_pred_class = np.where(y_pred >= 0, 1.0, -1.0)
    print(f"Accuracy: {accuracy_score(y_test, y_pred_class):.4f}")
    print(confusion_matrix(y_test, y_pred_class))

    print(np.unique(y_train, return_counts=True))
    print(np.unique(y_test, return_counts=True))

    print("Nonzero alpha:", np.sum(alpha > 1e-6))
    print("Free SV:", np.sum((alpha > 1e-6) & (alpha < 1.0 - 1e-6)))
    print("Alpha sum:", np.sum(alpha))
    print("Equality constraint:", np.dot(alpha, y_train))

    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
