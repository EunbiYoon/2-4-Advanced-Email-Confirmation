from ma import ma 
from models.confirmation import ConfirmationModel

class ConfirmationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model=ConfirmationModel

        # dont want to dump user
        load_only=("user",)

        # rest of this, do not want to load because of security
        dump_only=("id","expired_at","confirmed")
        
        # receive the confirmation foreign key is included dump
        include_fk=True

