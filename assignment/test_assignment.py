from collections import OrderedDict
import unittest
from mangrove.bootstrap import initializer
from mangrove.datastore.aggregationtree import AggregationTree
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity import Entity, get_by_short_code
from mangrove.datastore.entity_type import define_type, ENTITY_TYPE_TREE_ID
from mangrove.errors.MangroveException import DataObjectAlreadyExists
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import MOBILE_NUMBER_FIELD, NAME_FIELD, FormModel, get_form_model_by_code, FormSubmission, REGISTRATION_FORM_CODE, GlobalRegistrationFormSubmission, FormSubmissionFactory
from mangrove.transport.facade import TransportInfo, Request
from mangrove.transport.player.parser import OrderSMSParser
from mangrove.transport.player.player import SMSPlayer
from mangrove.transport.submissions import submission_count

class AssignmentTestCase(unittest.TestCase):
    def InitDb(self, server, database):
        self.manager = get_db_manager(server=server, database=database)
        _delete_db_and_remove_db_manager(self.manager)
        self.manager = get_db_manager(server=server, database=database)
        initializer.run(self.manager)


    def setUp(self):
        self.InitDb(server="http://localhost:5984", database="assignment")
        print "Connected to %s/%s" % (self.manager.url, self.manager.database_name)

        self.entity_type = ["School"]
        self.reporter_type=['reporter']
        self.phone_number_type = DataDictType(self.manager, name='Telephone Number', slug='telephone_number', primitive_type='string')
        self.first_name_type = DataDictType(self.manager, name='First Name', slug='first_name', primitive_type='string')
        self.default_ddtype = DataDictType(self.manager, name='Default String Datadict Type', slug='string_default', primitive_type='string')
        self.integer_ddtype = DataDictType(self.manager, name='Default Ingeger Datadict Type', slug='integer_default', primitive_type='number')
#        self.default_ddtype.save()

    def tearDown(self):
#        _delete_db_and_remove_db_manager(self.manager)
        pass


    def test_db_initializer(self):
        self.assertEqual("http://localhost:5984", self.manager.url)
        self.assertEqual("assignment", self.manager.database_name)


    def CreateSchoolEntityType(self):
        define_type(self.manager, self.entity_type)
        print "Entity Type is", self.entity_type

    def test_create_entity_type_named_school(self):
        paths = AggregationTree.get(self.manager, ENTITY_TYPE_TREE_ID, get_or_create=True).get_paths()
        self.assertNotIn(self.entity_type, paths)
        self.assertIn(['reporter'], paths)
        self.CreateSchoolEntityType()

        paths = AggregationTree.get(self.manager, ENTITY_TYPE_TREE_ID, get_or_create=True).get_paths()
        self.assertIn(self.entity_type, paths)

    def CreateSchool(self, data, id, short_code):
        school = Entity(self.manager, self.entity_type, data, id=id, short_code=short_code)
        school_id = school.save()
        school.add_data(data=[("SchoolID", id, self.default_ddtype),
                            ("SchollName", short_code, self.default_ddtype),
                            ("SchoolLocation", data, self.default_ddtype)])

        return school_id

    def CreateSchoolByFormModel(self):
        field1 = TextField(name="entity_question", code="i", label="What is scholl entity",language="en", entity_question_flag=True, ddtype=self.default_ddtype)
        field2 = TextField(name="School_name", code="n", label="What is scholl name",language="en", ddtype=self.default_ddtype)
        field3 = TextField(name="school_location", code="g", label="What is scholl location",language="en", ddtype=self.default_ddtype)
        field4 = TextField(name="school_type", code="t", label="What is scholl type",language="en", ddtype=self.default_ddtype)

        model = FormModel(self.manager, name="school", label="fds", form_code="School", entity_type=self.entity_type, is_registration_model=True, fields=[field1, field2, field3, field4])
        model.save()

        FormSubmission(model, OrderedDict({"i": "bh1", "n": "beihang", "g": ["beijing"], "t": "university"})).save(self.manager)
        FormSubmission(model, OrderedDict({"i": "qh1", "n": "qinghua", "g": ["beijing"], "t": "university"})).save(self.manager)
        FormSubmission(model, OrderedDict({"i": "bd1", "n": "beida", "g": ["beijing"], "t": "university"})).save(self.manager)

    def CreateSchoolByGlobalFormModel(self):
        global_form = get_form_model_by_code(self.manager, REGISTRATION_FORM_CODE)
        submission = OrderedDict({"t": self.entity_type, "n": "beihang-global", "s": "bh-g", "l": ["Global","China"],"m": "12345678987654321","g":(1,1)})
#        GlobalRegistrationFormSubmission(global_form, submission, errors=None).save(self.manager)

        FormSubmissionFactory().get_form_submission(global_form, submission).save(self.manager)

    def test_create_school_entity(self):
        school = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='BeiHang', short_code="bh")

        school = get_by_short_code(self.manager, "bh", self.entity_type)
        self.assertEqual(beihang_id, 'BeiHang')
        self.assertEqual(school.short_code, 'bh')


    def CreateReporter(self):
        reporter = Entity(self.manager, location=["China", "Beijing"], short_code="rpt_bj", id="Reporter001",
            entity_type=self.reporter_type)
        reporter.add_data(data=[(MOBILE_NUMBER_FIELD, "1234567890", self.phone_number_type),(NAME_FIELD, "001s", self.first_name_type)])
        reporter_id = reporter.save()
        return reporter_id, reporter

    def test_create_reporter(self):
        reporter_id,r = self.CreateReporter()
        self.assertEqual(reporter_id, 'Reporter001')

        reporter = get_by_short_code(self.manager, "rpt_bj", self.reporter_type)
        self.assertEqual(reporter.short_code, "rpt_bj")


    def CreateFormModel(self):
        question1 = TextField(name="entity_question", code="ID", label="What is the school reported on?", language="eng",entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="Your Name", code="Q1", label="What is your name", defaultValue="some default value", language="eng", ddtype=self.default_ddtype)
        question3 = IntegerField(name="Your Age", code="Q2", label="What is your age", ddtype=self.default_ddtype)
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color", options=[("RED", 1), ("YELLOW", 2)], ddtype=self.integer_ddtype)

        form_code = "form001"
        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="SCHOOL_FORM_MODEL", label="School form_model", form_code=form_code, type='survey',fields=[question1, question2, question3, question4])

        try:
            qid = self.form_model.save()
        except DataObjectAlreadyExists as e:
            get_form_model_by_code(self.manager, form_code).delete()
            qid = self.form_model.save()

        return form_code, qid

    def test_create_form_model(self):
        form_code, qid = self.CreateFormModel()

        form = get_form_model_by_code(self.manager, form_code)
        self.assertTrue(qid)
        self.assertEqual(form.form_code, form_code)

    def SendSubmission(self, message):
        sms_player = SMSPlayer(self.manager, location_tree=["China", "Beijing"], parser=(OrderSMSParser(self.manager)))
        transport_info = TransportInfo(transport="sms", source="1234567890", destination="5678")
        request = Request(message=message, transportInfo=transport_info)

        return sms_player.accept(request)

    def PrintResult(self, response):
        print "Submission: ", response.entity_type, response.form_code
        print "  Reporter:", response.reporters[0]['name']
        print "  Errors:",
        for questionid, error in response.errors.items():
            print questionid, error

        print "Accepted Answers:"
        for qid, value in response.processed_data.items():
            print qid, value

        print "  For school:", response.short_code
        print "Successfully!" if response.success else "Failed~"



    def test_sms_player(self):
        self.CreateSchoolEntityType()

        bh = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='BeiHang', short_code="bh")
        bh = get_by_short_code(self.manager, "bh", self.entity_type)
        print "Create School:", bh.short_code, bh.id

        bd_id = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='BeiDa', short_code="bd")
        bd = get_by_short_code(self.manager, "bd", self.entity_type)
        print "Create School:", bd.short_code, bd.id

        qh_id = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='QingHua', short_code="qh")
        qh = get_by_short_code(self.manager, "qh", self.entity_type)
        print "Create School:", qh.short_code, qh.id

        self.CreateSchoolByFormModel()
        self.CreateSchoolByGlobalFormModel()

        rpt_id, reporter = self.CreateReporter()
        print "Create Reporter:", reporter.short_code, reporter.id

        form_code, form_id = self.CreateFormModel()
        print "Create Questionnaire:", form_code, form_id

        self.PrintResult(self.SendSubmission("form001 bh zhangsan 22 RED"))

        self.PrintResult(self.SendSubmission("form001 bh lisi 23 2"))
        self.PrintResult(self.SendSubmission("form001 bd wangwu 27 1"))
        self.PrintResult(self.SendSubmission("form001 bd zhaoliu 25 1"))
        self.PrintResult(self.SendSubmission("form001 qh zhouqi 24 2"))
        self.PrintResult(self.SendSubmission("form001 qh zhengba 30 1"))

        count = submission_count(self.manager, "form001", None, None)
        self.assertEqual(6, count)















