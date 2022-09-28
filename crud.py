from ast import And

from sqlalchemy.orm import Session

import models
import schemas
from models import Experiment
import os
from fastapi import File, UploadFile
import shutil


def get_projects(db: Session):
    return db.query(models.Project).all()


def get_project(db: Session, id: int):
    return db.query(models.Project).filter(models.Project.project_id == id).first()


def get_project_by_name(db: Session, name: str):
    return db.query(models.Project).filter(models.Project.project_name == name).first()


def create_project(db: Session, project: schemas.ProjectCreate):

    db_project = models.Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_experiments(db: Session):
    return db.query(models.Experiment).all()


def get_exp_by_name(db: Session, name: str, id: int):
    return db.query(models.Experiment).filter(models.Experiment.project_id == id, models.Experiment.experiment_name == name).first()


def create_project_experiment(db: Session, experiment: schemas.ExperimentCreate, project_id: int):

    db_exp = models.Experiment(**experiment.dict(), project_id=project_id)
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)
    expname = db_exp.experiment_name

    projname = db.query(models.Project).filter(
        models.Project.project_id == project_id).first()
    projname = projname.project_name
    os.mkdir(f'projects/{projname}/{expname}')

    os.mkdir(f'projects/{projname}/{expname}/runs')

    return db_exp


def update_config_path(db: Session, expno: int, dir: str):

    item_to_update = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == expno).first()
    item_to_update.experiment_config_path = dir

    db.commit()

    return item_to_update

def update_token(db: Session, expno: int):
    exp_uuid = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == expno).first()
    exp_uuid = exp_uuid.uuid
    ip = '127.0.0.1'
    port = '8000'
    delim = "+"
    token = str(exp_uuid) + delim + ip + delim +  port
    exptoken = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == expno).first()
    exptoken.token = token

    db.commit()
    return token
    

def update_configuration(db: Session, expno: int):

    config = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == expno).first()
    config.experiment_config = True

    db.commit()

    return config


def delete_experiment(db: Session, exp_id: int):
    obj = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == exp_id).first()

    experiment_name = obj.experiment_name

    project_name = db.query(models.Project).filter(
        models.Project.project_id == obj.project_id).first()
    project_name = project_name.project_name

    db.delete(obj)
    db.commit()

    path = f'projects/{project_name}/{experiment_name}'
    shutil.rmtree(path, ignore_errors=False, onerror=None)

    return f"Experiment {obj.experiment_name} deleted"


def delete_project(db: Session, proj_id: int):
    obj = db.query(models.Project).filter(
        models.Project.project_id == proj_id).first()
    project_name = obj.project_name

    db.delete(obj)
    db.commit()

    path = f'projects/{project_name}'
    shutil.rmtree(path, ignore_errors=False, onerror=None)
    return f"Project {obj.project_name} deleted"


def save_file(db: Session, experiment_no: int, uploaded_file: File(...)):
    experiment = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == experiment_no).first()
    experiment_name = experiment.experiment_name

    project_name = db.query(models.Project).filter(
        models.Project.project_id == experiment.project_id).first()
    project_name = project_name.project_name

    file_location = f"projects/{project_name}/{experiment_name}/{uploaded_file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(uploaded_file.file.read())

    if  uploaded_file.endswith('.h5')::
        #zip
    return "file uploaded"


def create_config_file(db: Session, model: schemas.CreateConfigFile, project_name: str, experiment_name: str):
    model_type = model.model_type
    experiment_domain = model.epxeriment_domain
    experiment_name = experiment_name
    project_name = project_name

    DATA = {}
    DATA["Model Type"] = model_type
    DATA["Experiment Domain"] = experiment_domain
    DATA["Experiment name"] = experiment_name
    DATA["Project Name"] = project_name
    return DATA


def get_runs(db: Session):
    return db.query(models.Run).all()


def create_run(db: Session, run: schemas.RunCreate, experiment_no: int):

    db_run = models.Run(**run.dict(), experiment_no=experiment_no)
    num = db.query(models.Run).filter(models.Run.experiment_no ==experiment_no ).count()

    db_run.run_name = f'run{num+1}'
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    
    runname = db_run.run_name

    exp = db.query(models.Experiment).filter(models.Experiment.experiment_no == experiment_no).first()
    
    expname = exp.experiment_name
    project_id = exp.project_id

    projname = db.query(models.Project).filter(
        models.Project.project_id == project_id).first()
    projname = projname.project_name


    os.mkdir(f'projects/{projname}/{expname}/runs/{runname}')

    return db_run

def update_run_config(db: Session, run_no: int):

    config = db.query(models.Run).filter(
        models.Run.run_no == run_no).first()
    config.config_value = True

    db.commit()
     
    return 'configured'


def create_run_config_file(db: Session, model: schemas.CreateRunConfigFile):
    no_of_epoch = model.no_of_epoch
    batch_size = model.batch_size
    field_1 = model.field_1
    field_2 = model.field_2

    DATA = {}
    DATA["number of epoch"] = no_of_epoch
    DATA["Batch Size"] = batch_size
    DATA["Field 1"] = field_1
    DATA["Field 2"] = field_2
    return DATA


def update_run_config_path(db: Session, run_no: int, dir: str):

    item_to_update = db.query(models.Run).filter(
        models.Run.run_no == run_no).first()
    item_to_update.run_config_path = dir

    db.commit()

    return item_to_update