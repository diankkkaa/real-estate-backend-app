from . import db
from sqlalchemy import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship


class Administrator(db.Model):
    __tablename__ = 'Administrators'
    administrator_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Photo(db.Model):
    __tablename__ = 'Photos'
    photo_id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('Objects.object_id', ondelete='CASCADE'))
    file_path = db.Column(db.String, nullable=False)


class Object(db.Model):
    __tablename__ = 'Objects'

    object_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), nullable=False)
    rooms = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=True)
    total_floors = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    heating = db.Column(db.String(50), nullable=False)
    balcony = db.Column(db.Boolean, nullable=False, default=False)
    square = db.Column(db.Numeric(10, 2), nullable=False)
    price = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    code = db.Column(db.Integer, nullable=False, unique=True)
    created_date = db.Column(db.Date, nullable=False)

    photos = relationship('Photo', backref='object', lazy='dynamic')

    @hybrid_property
    def price_per_sq_meter(self):
        if self.square > 0:
            return round(self.price / self.square, 2)
        return None

    __table_args__ = (
        CheckConstraint("type IN ('квартира', 'будинок')", name='check_type'),
        CheckConstraint("category IN ('новобудова', 'стародавня будівля')", name='check_category'),
        CheckConstraint("heating IN ('централізоване', 'автономне', 'індивідуальне')", name='check_heating'),
        CheckConstraint("status IN ('доступний', 'проданий')", name='check_status'),
    )

    def get_photos(self):
        return [photo.file_path for photo in self.photos]
