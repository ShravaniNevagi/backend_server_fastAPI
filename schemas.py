from sqlite3 import Timestamp
import string
from tokenize import String
from typing import List, Union
from xmlrpc.client import Boolean

from pydantic import BaseModel



class Client(BaseModel):
    client_no:int
    client_name:str
    token:str
    
    ipaddress:str
    port:str


    class Config:
        orm_mode = True

class RunConfigBase(BaseModel):
    batch_size: int
    ip: str
    port: str
    no_of_epoch: int


class CreateRunConfigFile(RunConfigBase):
    pass



class RunBase(BaseModel):
    pass


class RunCreate(RunBase):
    pass


class Run(RunBase):
    run_no: int
    experiment_no: int
    run_name: str

    class Config:
        orm_mode = True


class ExperimentBase(BaseModel):
    experiment_name: str


class ExperimentCreate(ExperimentBase):
    pass


class Experiment(ExperimentBase):
    experiment_no: int
    project_id: int
    experiment_config: Boolean
    token: str
    runs: List[Run] = []
    clients: List[Client] = []

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    project_name: str


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    project_id: int

    experiments: List[Experiment] = []

    class Config:
        orm_mode = True


class ConfigBase(BaseModel):
    model_type: str
    epxeriment_domain: str


class CreateConfigFile(ConfigBase):
    pass