from sklearn.model_selection import train_test_split

from evaluations import ROC_PR
import keras.backend as K
from models.model_gene_based import prepare_data
from tensorflow import keras

import numpy as np


def masked_loss_function(y_true, y_pred):
    mask = K.cast(K.not_equal(y_true, -1), K.floatx())
    return K.binary_crossentropy(y_true * mask, y_pred * mask)


def masked_accuracy(y_true, y_pred):
    dtype = K.floatx()
    total = K.sum(K.cast(K.not_equal(y_true, -1), dtype))
    correct = K.sum(K.cast(K.equal(y_true, K.round(y_pred)), dtype))
    return correct / total


def run_ELI5(model, X_train, X_test, X_val, y_train, y_test, y_val):
    X_train2 = np.array(X_train).astype(np.float)
    X_test2 = np.array(X_test).astype(np.float)
    X_val2 = np.array(X_val).astype(np.float)

    y_train2 = np.array(y_train).astype(np.float)
    y_test2 = np.array(y_test).astype(np.float)
    y_val2 = np.array(y_val).astype(np.float)

    score = ROC_PR.ROC_Score(model, X_val2, y_val2)
    score_test = ROC_PR.ROC_Score(model, X_test2, y_test2)
    # score_for_each_drug = ROC_PR.ROC(model, X_test2, y_test2, ("LRCN" + "BO_delete"), True)
    spec_recall, prec_recall = ROC_PR.PR(model, X_test2, y_test2)

    print('area under ROC curve for val:', score)
    print('area under ROC curve for test:', score_test)
    print("recall at 95 spec: ", spec_recall)
    print("precision recall: ", prec_recall)

    def score(X_test, y_test):
        return ROC_PR.ROC_Score(model, X_test, y_test)

    from eli5.permutation_importance import get_score_importances

    feature_score = []

    for i in range(0, len(X_test2[0])):
        lst = []
        lst.append(i)
        base_score, score_decreases = get_score_importances(score, X_test2, y_test2, n_iter=1, columns_to_shuffle=lst)
        feature_importances = np.mean(score_decreases, axis=0)
        feature_score.append(feature_importances[0])
        print(i)

    print(feature_score)


def load_model(i):
    new_model = keras.models.load_model('saved_models/lrcn_' + str(i) + '.h5',
                                        custom_objects={'masked_loss_function': masked_loss_function,
                                                        'masked_accuracy': masked_accuracy})
    return new_model


def prepare_data(features, label):
    y = []
    for i in range(0, len(label)):
        label[i] = label[i].values.tolist()

    for j in range(0, len(label[0])):
        tmp = []
        for i in range(0, len(label)):
            if label[i][j][0] != 0.0 and label[i][j][0] != 1.0:
                tmp.extend([-1])
            else:
                tmp.extend(label[i][j])
        y.append(tmp)

    X = features.values.tolist()

    X = np.array(X)
    y = np.array(y)
    return X, y


def run_feature_importance(df_train, labels):
    X, y = prepare_data(df_train, labels)

    for i in range(0, 10):
        print("fold: " + str(i))
        length = int(len(X) / 10)
        if i == 0:
            X_train = X[length:]
            X_test = X[0:length]
            y_train = y[length:]
            y_test = y[0:length]
        elif i != 9:
            X_train = np.append(X[0:length * i], X[length * (i + 1):], axis=0)
            X_test = X[length * i:length * (i + 1)]
            y_train = np.append(y[0:length * i], y[length * (i + 1):], axis=0)
            y_test = y[length * i:length * (i + 1)]
        else:
            X_train = X[0:length * i]
            X_test = X[length * i:]
            y_train = y[0:length * i]
            y_test = y[length * i:]

        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.1, random_state=1, shuffle=False)
        model = load_model(i)
        run_ELI5(model, X_train, X_test, X_val, y_train, y_test, y_val)