
from sqlalchemy.orm import Session

import models
import schemas

import os
from fastapi import File, UploadFile
import shutil
import pathlib
import zipfile
import docker
import json
import requests

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
    import uuid
    
    projname = db.query(models.Project).filter(
        models.Project.project_id == project_id).first()
    projname = projname.project_name
    
    
    #uuid.uuid3(uuid.NAMESPACE_URL, {projectname} + {experimentname}))
    id = uuid.uuid4()
    ip = '127.0.0.1'
    port = '8000'
    delim = "+"
    
    
    db_exp = models.Experiment(**experiment.dict(), project_id=project_id)
    db.add(db_exp)
    # db_exp.token = token
    db.commit()
    db.refresh(db_exp)
    expname = db_exp.experiment_name
    expid = db_exp.experiment_no

    name = str(projname) + delim + str(expname)

    token = str(uuid.uuid3(uuid.NAMESPACE_URL, name)) + delim + str(id) + delim + ip + delim + port

    db_token = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == expid).first()
    db_token.token = token

    db.commit()
    db.refresh(db_token)
    os.mkdir(f'projects/{projname}/{expname}')

    os.mkdir(f'projects/{projname}/{expname}/runs')

    return db_exp


def update_config_path(db: Session, expno: int, dir: str):

    item_to_update = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == expno).first()
    item_to_update.experiment_config_path = dir

    db.commit()

    return item_to_update



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
    file_extension = pathlib.Path(f'{file_location}').suffix
        
    with open(file_location, "wb+") as file_object:
        file_object.write(uploaded_file.file.read())

    if file_extension == '.h5':
        os.rename(rf'{file_location}',rf'projects/{project_name}/{experiment_name}/model.h5')
    if file_extension == '.py':
        os.rename(rf'{file_location}',rf'projects/{project_name}/{experiment_name}/loader.py')
    if file_extension == '.npz':
        os.rename(rf'{file_location}',rf'projects/{project_name}/{experiment_name}/test_data.npz')

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

def get_runs_by_expno(db: Session, experiment_no:int):
    return db.query(models.Run).filter(
        models.Run.experiment_no == experiment_no).all()

def create_run(db: Session, run: schemas.RunCreate, experiment_no: int):

    db_run = models.Run(**run.dict(), experiment_no=experiment_no)
    num = db.query(models.Run).filter(
        models.Run.experiment_no == experiment_no).count()

    db_run.run_name = f'run{num+1}'
    db.add(db_run)
    db.commit()
    db.refresh(db_run)

    runname = db_run.run_name

    exp = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == experiment_no).first()

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


def create_run_config_file(db: Session, model: schemas.CreateRunConfigFile,runname:str,expname:str,rundir:str,expdir:str):
    no_of_epoch = model.no_of_epoch
    batch_size = model.batch_size
    ip = model.ip
    port = model.port
    no_of_rounds = model.no_of_rounds


    DATA = {}
    DATA["number_of_epochs"] = no_of_epoch
    DATA["batch_size"] = batch_size
    DATA["ipaddress"] = ip
    DATA["port"] = port
    DATA["experiment_name"] = expname
    DATA["run_name"] = runname
    DATA["run_path"] = rundir
    DATA["experiment_path"] = expdir
    DATA["number_of_rounds"] = no_of_rounds
    return DATA


def update_run_config_path(db: Session, run_no: int, dir: str):

    item_to_update = db.query(models.Run).filter(
        models.Run.run_no == run_no).first()
    item_to_update.run_config_path = dir

    db.commit()

    return item_to_update



def zipfiles(db: Session, experiment_no: int):

    obj = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == experiment_no).first()

    experimentname = obj.experiment_name

    project_name = db.query(models.Project).filter(
        models.Project.project_id == obj.project_id).first()
    projectname = project_name.project_name
    
    with zipfile.ZipFile(f'projects/{projectname}/{experimentname}/archives.zip', 'w',
                        compression=zipfile.ZIP_DEFLATED, #compression method - Usual ZIP compression
                        compresslevel=9) as zf:
        path = f'projects/{projectname}/{experimentname}/'
        root = 'projects/'
        for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.json') or file.endswith('.h5') or file.endswith('.py'):
                        
                        zf.write(os.path.join(root, file))
        
        
        
        #zf.write(f'projects/{projectname}/{experimentname}/file.json', arcname='file.json')
        #zf.write(f'projects/{projectname}/{experimentname}/file.h5', arcname='file.h5')

   
    return 'success'



def get_tokens(token:str, db:Session):
    return db.query(models.Experiment).filter(models.Experiment.token == token).first()


def add_client(port:str,ipaddress:str,token:str,client_name:str,db: Session):

    # models.Client.client_name = client_name
    # models.Client.token = token
    # models.Client.port = port
    # models.Client.ipaddress = ipaddress
    
    db_client = models.Client(client_name = client_name,token = token,port = port,ipaddress = ipaddress)
    db.add(db_client)
    db.commit()

    return 


def check_token(token:str, db:Session):
    return db.query(models.Client).filter(models.Client.token == token).first()


def get_exp_by_token(db: Session, token:str):
    return db.query(models.Experiment).filter(models.Experiment.token == token).first()



def start_run(db: Session,model:schemas.RunClients):

    

    token = model.token
    path = db.query(models.Experiment).filter(models.Experiment.token == token).first()
    path = path.experiment_config_path

    run_path = path + '/runs/'+ model.run_name

    with open(run_path+'/runs_config.json') as f:
        runs_config = json.load(f)

    runs_config['number_of_clients']=len(model.client_ip)
    experiment_path=os.getcwd() + '/'+runs_config['experiment_path']

    with open(run_path+'/runs_config.json', 'w') as f:
        json.dump(runs_config,f)

    # client = docker.from_env()
    # container = client.containers.run(image = 'flower_tensorflow_server',network='host', environment = ['RUN_PATH=runs/'+model.run_name+'/'],volumes = {experiment_path:{'bind':'/app/dir/','mode': 'rw'}},detach=True,remove=True)
    # while(True):
    #     if 'FL starting' in str(container.logs()):
    #         print('FL starting')
    #         break
    endpoint_url = 'start_client/'
    payload = {'token':token, 'run_name' : model.run_name, 'runs_config':runs_config}
    for i in range(len(model.client_ip)):
            url = f'http://{model.client_ip[i]}:{model.client_port[i]}/{endpoint_url}'
            r = requests.post(url, json = payload)

    
        

    # docker run -it --network host -e RUN_PATH='runs/run1/' -v /home/sashreek/temp/experiment_agg:/app/dir/ server bash

    return 
