from flask_mongoengine import Document, MongoEngine

class City(Document):
    name = MongoEngine().StringField(required=True)
    meta = {'collection': 'cities'} 

    def to_json(self):
        return {"name": self.name}