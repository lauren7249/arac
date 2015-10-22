from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import classification_report
from sklearn.svm import SVC, LinearSVC
import pandas
from sklearn.externals import joblib
from sklearn.cross_validation import KFold
from boto.s3.key import Key
from boto.s3.connection import S3Connection

AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')

def create_model(training_file):
	names = ["same_school_id_year","weight_school_id_year","same_company_id_year","weight_company_id_year","same_company_id_location_year","weight_company_id_location_year","connection"]
	#data = pandas.read_csv(training_file, delimiter=",", skiprows=150000, names=names)
	data = pandas.read_csv(training_file, delimiter=",")
	print len(data.index)
	data = data.ix[(data["same_school_id_year"]==1) | (data["same_company_id_year"]==1)]
	print len(data.index)

	print len(data.columns)
	data = data[names]
	print len(data.columns)
	
	y = data["connection"]=='T'
	X = data.drop('connection', 1)
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=0)
	#print X.head()
	#print y.head()
	# Set the parameters by cross-validation
	#tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-3, 1e-4],'C': [1, 10, 100, 1000],'class_weight':['auto']},{'kernel': ['linear'], 'C': [1, 10, 100, 1000],'class_weight':['auto']}]
	tuned_parameters = [{'C': [1, 10, 100, 1000],'class_weight':['auto']}]

	cv = KFold(X_train.shape[0], 5, shuffle=True, random_state=33)
	clf = GridSearchCV(LinearSVC(C=1), tuned_parameters, cv=cv, scoring='roc_auc')
	clf.fit(X_train, y_train)
	y_true, y_pred = y_test, clf.predict(X_test)
	joblib.dump(clf, 'model.txt', compress=1) 	
	joblib.dump(classification_report(y_true, y_pred), 'GridSearchCV_report.txt', compress=1) 

	k = Key(bucket)
	k.key = "/models/GridSearchCV.model" 
	k.set_contents_from_filename("model.txt")		

	k = Key(bucket)
	k.key = "/models/GridSearchCV.report" 
	k.set_contents_from_filename("GridSearchCV_report.txt")		

	predictors = list(X.columns.values)
	joblib.dump(predictors, 'predictors.txt', compress=1) 	
	k = Key(bucket)
	k.key = "/models/model_predictors" 
	k.set_contents_from_filename("predictors.txt")	
	print predictors

if __name__ == "__main__":
	create_model("https://s3.amazonaws.com/advisorconnect-bigfiles/truth/training_data.csv")	