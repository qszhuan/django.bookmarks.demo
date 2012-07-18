from collections import OrderedDict
from mangrove.errors.MangroveException import DataObjectAlreadyExists
from mangrove.datastore.entity_type import *
from mangrove.form_model.form_model import FormModel, get_form_model_by_code, FormSubmissionFactory
from mangrove.datastore.database  import DatabaseManager
from mangrove.form_model.field import *
from mangrove.bootstrap import initializer


def InitializeDB():
    dbm = DatabaseManager(server="http://localhost:5984", database="assignment")
    print "Connected to", dbm.url, dbm.database_name
    initializer.run(dbm)
    return dbm


dbm = InitializeDB()

#exit(0)
#define_type
def SaveQuestionnaire(dbm):
    entity_type = ['school']
    if not entity_type_already_defined(dbm, entity_type):
        define_type(dbm, entity_type)

    #default_ddtype
    default_ddtype = DataDictType(dbm, name='Default String Datadict Type', slug='string_default',
        primitive_type='string')
    #questions
    question0 = TextField(name="Q0", code="ID", label="What is your id?", entity_question_flag=True,
        ddtype=default_ddtype)
    question1 = TextField(name="Q1", code="FIRSTNAME", label="What is your first name?", entity_question_flag=False,
        ddtype=default_ddtype)
    question2 = TextField(name="Q2", code="LASTNAME", label="What is your last name?", entity_question_flag=False,
        ddtype=default_ddtype)
    question3 = DateField(name="Q3", code="BIRTHDATE", date_format='mm.yyyy', label="What is your birth date?",
        ddtype=default_ddtype)
    question4 = TextField(name="Q4", code="COMMENT", label="What do you want to add?", entity_question_flag=False,
        ddtype=default_ddtype)
    #form_model
    form_model = FormModel(dbm, entity_type=entity_type, name="Personal information Survey", label="Basic Info Survey",
        form_code="PISurvey", type='survey', fields=[question0, question1, question2, question3, question4])
    try:
        qid = form_model.save()
    except DataObjectAlreadyExists as e:
        get_form_model_by_code(dbm, "PISurvey").delete()
        qid = form_model.save()
    return form_model

form_model = SaveQuestionnaire(dbm)

#exit(0)
answers = OrderedDict({"ID" : "111", "FIRSTNAME":"Qingshan", "LASTNAME":"Zhuan",  "BIRTHDATE" : "2000000","COMMENT":"Learning mangrove now."})

cleaned_values, errors = form_model.validate_submission(answers)
for i in cleaned_values:
    print "cleaned value:", i
for i in errors:
    print "error:", i

form = get_form_model_by_code(dbm, form_model.form_code)
print "form id is:", form.id

for field in form.fields:
    print field.name, field.label, field.type, field.code


form_submission = FormSubmissionFactory().get_form_submission(form, answers)
form_submission.save(dbm)



