from flask import has_app_context, current_app as app
from pymongo import MongoClient


class MongoDB:
    _instance = None
    _client = None
    _db = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)

        return cls._instance

    @classmethod
    def _initialize(cls):
        if not has_app_context():
            raise RuntimeError("Application context is required to initialize MongoDB")

        if cls._instance._client is None or cls._instance._db is None:
            cls._instance._client = MongoClient(app.config['MONGO_URI'])
            cls._instance._db = cls._instance._client.get_default_database()

    @classmethod
    def create_instance(cls):
        instance = cls.__new__(cls)
        instance._initialize()

    @classmethod
    def get_collection(cls, collection_name: str):
        cls.create_instance()
        return cls._instance._db[collection_name]
        
