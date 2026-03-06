from pydantic import BaseModel, ConfigDict


class AbstractBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AbstractReadBaseModel(BaseModel):
    pass


class AbstractCreateBaseModel(BaseModel):
    pass


class AbstractUpdateBaseModel(BaseModel):
    pass


class AbstractDeleteBaseModel(BaseModel):
    pass


class AbstractDefaultBaseModel(BaseModel):
    pass


class AbstractReadPagginationBaseModel(BaseModel):
    pass


class AbstractDefaultPagginationBaseModel(BaseModel):
    pass
