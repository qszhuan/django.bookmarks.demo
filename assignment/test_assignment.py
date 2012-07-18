import unittest
from mangrove.bootstrap import initializer
from mangrove.datastore.aggregationtree import AggregationTree
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity import Entity, get_by_short_code
from mangrove.datastore.entity_type import define_type, ENTITY_TYPE_TREE_ID
from mangrove.errors.MangroveException import DataObjectAlreadyExists
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import MOBILE_NUMBER_FIELD, NAME_FIELD, FormModel, get_form_model_by_code
from mangrove.form_model.location import Location
from mangrove.transport.facade import TransportInfo, Request
from mangrove.transport.player.parser import OrderSMSParser
from mangrove.transport.player.player import SMSPlayer
from mangrove.transport.submissions import submission_count
from mock import self

class AssignmentTestCase(unittest.TestCase):
    def InitDb(self, server, database):
        self.manager = get_db_manager(server=server, database=database)
        initializer.run(self.manager)

    def setUp(self):
        self.InitDb(server="http://localhost:5984", database="assignment")
        self.entity_type = ["School"]
        self.reporter_type=['reporter']
        self.phone_number_type = DataDictType(self.manager, name='Telephone Number', slug='telephone_number', primitive_type='string')
        self.first_name_type = DataDictType(self.manager, name='First Name', slug='first_name', primitive_type='string')
        self.default_ddtype = DataDictType(self.manager, name='Default String Datadict Type', slug='string_default', primitive_type='string')
#        self.default_ddtype.save()

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.manager)
        pass


    def test_db_initializer(self):
        self.assertEqual("http://localhost:5984", self.manager.url)
        self.assertEqual("assignment", self.manager.database_name)


    def CreateSchoolEntityType(self):
        define_type(self.manager, self.entity_type)

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
        return school_id

    def test_create_school_entity(self):
        beihang_id = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='BeiHang', short_code="bh")

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
        question1 = TextField(name="entity_question", code="ID", label="What is the school reported on?", language="eng"
            ,
            entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="Your Name", code="Q1", label="What is your name", defaultValue="some default value",
            language="eng", ddtype=self.default_ddtype)
        question3 = IntegerField(name="Your Age", code="Q2", label="What is your age", ddtype=self.default_ddtype)
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
            options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)
        form_code = "form001"
        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="School form_model",
            form_code=form_code, type='survey',
            fields=[question1, question2, question3, question4], )
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
        sms_parser = OrderSMSParser(self.manager)
        sms_player = SMSPlayer(self.manager, location_tree=["China", "Beijing"], parser=sms_parser)
        transport_info = TransportInfo(transport="sms", source="1234567890", destination="5678")
        request = Request(message=message, transportInfo=transport_info)
        player_accept = sms_player.accept(request)
        return player_accept

    def test_sms_player(self):
        self.CreateSchoolEntityType()
        bh_id = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='BeiHang', short_code="bh")
        bd_id = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='BeiDa', short_code="bd")
        qh_id = self.CreateSchool(data=['China', 'Beijing', 'HaiDian'], id='QingHua', short_code="qh")
        rpt_id, reporter = self.CreateReporter()
        form_code, form_id = self.CreateFormModel()

        player_accept = self.SendSubmission("form001 bh zhangsan 22 1")
        player_accept = self.SendSubmission("form001 bh lisi 23 2")
        player_accept = self.SendSubmission("form001 bd wangwu 27 1")
        player_accept = self.SendSubmission("form001 bd zhaoliu 25 1")
        player_accept = self.SendSubmission("form001 qh zhouqi 24 2")
        player_accept = self.SendSubmission("form001 qh zhengba 30 1")

        count = submission_count(self.manager, "form001", None, None)
        self.assertEqual(6, count)















