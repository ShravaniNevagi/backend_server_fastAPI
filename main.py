from fastapi.middleware.cors import CORSMiddleware
import http
from typing import List
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import SessionLocal, engine
import os
import json

from fastapi import File, UploadFile
from fastapi.responses import FileResponse


models.Base.metadata.create_all(bind=engine)



app = FastAPI()


origins = ['*']


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"go to ": "http://127.0.0.1:8000/docs"}


@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(db: Session = Depends(get_db)):
    projects = crud.get_projects(db)
    return projects


@app.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, id=id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db_project


@app.get("/experiments/", response_model=List[schemas.Experiment])
def read_experiments(db: Session = Depends(get_db)):
    experiment = crud.get_experiments(db)
    return experiment


@app.post("/projects/{project_id}/experiments/", status_code=status.HTTP_201_CREATED, response_model=schemas.Experiment)
def create_exp_under_project(project_id: int, experiment: schemas.ExperimentCreate, db: Session = Depends(get_db)):

    db_exp = crud.get_exp_by_name(
        db, id=project_id, name=experiment.experiment_name)

    if db_exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"exp with name {experiment.experiment_name} already exists")

    return crud.create_project_experiment(db=db, experiment=experiment, project_id=project_id)


@app.post("/projects/", status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, experiment: schemas.ExperimentCreate, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_name(db, name=project.project_name)

    if db_project:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"project with name {project.project_name} already exists")

    proj = crud.create_project(db=db, project=project)
    projname = proj.project_name
    os.mkdir(f'projects/{projname}')
    pid = proj.project_id

    crud.create_project_experiment(
        db=db, experiment=experiment, project_id=pid)

    return pid


@app.put("/experiments/config/step1", status_code=status.HTTP_202_ACCEPTED)
def create_config_file(expno: int, model: schemas.CreateConfigFile, db: Session = Depends(get_db)):

    experiment = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == expno).first()
    experiment_name = experiment.experiment_name

    project_name = db.query(models.Project).filter(
        models.Project.project_id == experiment.project_id).first()
    project_name = project_name.project_name

    dir = f'projects/{project_name}/{experiment_name}'
    FILE = dir + '/experiment_config.json'

    DATA = crud.create_config_file(
        db=db, model=model, experiment_name=experiment_name, project_name=project_name)

    DATA = json.dumps(DATA)
    _ = open(FILE, mode='w+').write(DATA)

    with open(FILE) as file:
        result = json.load(file)

    add_path = crud.update_config_path(
        expno=expno, db=db, dir=dir)
    return "configured"


# @app.post("/experiments/config/step2/upload_file1", status_code=status.HTTP_202_ACCEPTED)
# async def upload_file1(experiment_no: int, uploaded_file: UploadFile = File(...), db: Session = Depends(get_db)):
#     return crud.save_file(db=db, experiment_no=experiment_no, uploaded_file=uploaded_file)


# @app.post("/experiments/config/step2/upload_file2", status_code=status.HTTP_202_ACCEPTED)
# async def upload_file2(experiment_no: int, uploaded_file: UploadFile = File(...), db: Session = Depends(get_db)):
#     return crud.save_file(db=db, experiment_no=experiment_no, uploaded_file=uploaded_file)


# @app.post("/experiments/config/step2/upload_file3", status_code=status.HTTP_202_ACCEPTED)
# async def upload_file3(experiment_no: int, uploaded_file: UploadFile = File(...), db: Session = Depends(get_db)):
#     return crud.save_file(db=db, experiment_no=experiment_no, uploaded_file=uploaded_file)


# @app.post("/experiments/uploads/", status_code=status.HTTP_202_ACCEPTED)
# async def upload_file3(experiment_no:int, uploaded_file1: UploadFile = File(...), uploaded_file2: UploadFile = File(...), uploaded_file3: UploadFile = File(...), db:Session = Depends(get_db)):
#     crud.save_file(db=db,experiment_no=experiment_no, uploaded_file=uploaded_file1)
#     crud.save_file(db=db,experiment_no=experiment_no, uploaded_file=uploaded_file2)
#     crud.save_file(db=db,experiment_no=experiment_no, uploaded_file=uploaded_file3)
#     return 'done'
# @app.post("expereiments/upload_files")
# async def create_upload_files(experiment_no: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):

#     for file in files:

#         crud.save_file(db=db, experiment_no=experiment_no, uploaded_file=file)

#     return {"Result": "OK", "filenames": [file.filename for file in files]}

@app.post("/experiments/config/step2/upload-files")
async def create_upload_files(experiment_no: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):

    for file in files:

        crud.save_file(db=db, experiment_no=experiment_no, uploaded_file=file)

    # exp = db.query(models.Experiment).filter(
    #     models.Experiment.experiment_no == experiment_no).first()

    # exp_uuid = exp.uuid

    # experiment_name = exp.experiment_name

    # project_name = db.query(models.Project).filter(
    #     models.Project.project_id == exp.project_id).first()

    # project_name = project_name.project_name

    # count = 0

    # dir = f'projects/{project_name}/{experiment_name}'
    # print(dir)
    # for path in os.listdir(dir):

    #     # check if current path is a file

    #     if os.path.isfile(os.path.join(dir, path)):

    #         count += 1

    #         if count == 2:

    #             config_path = crud.update_configuration(
    #                 expno=experiment_no, db=db)

    # return {"Result": "OK", "filenames": [file.filename for file in files], 'uuid': exp_uuid}
    return {"Result": "OK", "filenames": [file.filename for file in files]}


# @app.put("/experiments/config/step3/", status_code=status.HTTP_200_OK)
# def generate_uuid(expno: int, db: Session = Depends(get_db)):

#     config_path = crud.update_configuration(expno=expno, db=db)

#     exp_uuid = db.query(models.Experiment).filter(
#         models.Experiment.experiment_no == expno).first()
#     exp_uuid = exp_uuid.uuid

#     # config_path = crud.update_configuration(expno=expno, db=db)

#     return exp_uuid


@app.put("/experiments/config/generate_token/", status_code=status.HTTP_200_OK)
def get_token(expno: int, db: Session = Depends(get_db)):
    crud.zipfiles(db=db,experiment_no=expno)
    config_path = crud.update_configuration(expno=expno, db=db)
    token = db.query(models.Experiment).filter(models.Experiment.experiment_no == expno).first()
    return token.token


@app.delete("/experiments/delete_experiment/", status_code=status.HTTP_200_OK)
def delete_experiment(exp_id: int, db: Session = Depends(get_db)):
    db_exp = db.query(models.Experiment).get(exp_id)

    if not db_exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return crud.delete_experiment(db=db, exp_id=exp_id)


@app.delete("/projects/delete_project/", status_code=status.HTTP_200_OK)
def delete_project(proj_id: int, db: Session = Depends(get_db)):
    db_proj = db.query(models.Project).get(proj_id)

    if not db_proj:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.delete_project(db=db, proj_id=proj_id)


@app.get("/experiments/get_config/")
def check_config_value(experiment_no: int, db: Session = Depends(get_db)):

    exp_config_value = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == experiment_no).first()
    if exp_config_value is None:
        raise HTTPException(status_code=404, detail="experiment not found")

    exp_config_value = exp_config_value.experiment_config
    return exp_config_value


@app.get("/runs/", response_model=List[schemas.Run])
def read_runs(db: Session = Depends(get_db)):
    run = crud.get_runs(db)
    return run

@app.get("/runs/{experiment_no}", response_model=List[schemas.Run])
def get_runs_by_expid(id: int, db: Session = Depends(get_db)):
    run = crud.get_runs_by_expno(db, experiment_no=id)
    return run

@app.post("/projects/experiments/{experiment_no}/runs", status_code=status.HTTP_201_CREATED, response_model=schemas.Run)
def create_run_under_experiment(experiment_no: int, run: schemas.RunCreate, db: Session = Depends(get_db)):
    return crud.create_run(db=db, experiment_no=experiment_no, run=run)


@app.get("/runs/get_config/")
def check_run_config_value(run_no: int, db: Session = Depends(get_db)):

    run_config_value = db.query(models.Run).filter(
        models.Run.run_no == run_no).first()

    if run_config_value is None:
        raise HTTPException(status_code=404, detail="run not found")

    run_config_value = run_config_value.config_value
    return run_config_value


@app.put("/runs/config/step2/", status_code=status.HTTP_200_OK)
def update_run_config_value(run_no: int, db: Session = Depends(get_db)):

    return crud.update_run_config(run_no=run_no, db=db)


@app.put("/runs/config/step1/", status_code=status.HTTP_202_ACCEPTED)
def create_config_file(run_no: int, model: schemas.CreateRunConfigFile, db: Session = Depends(get_db)):
    run = db.query(models.Run).filter(
        models.Run.run_no == run_no).first()

    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    run_name = run.run_name

    experiment = db.query(models.Experiment).filter(
        models.Experiment.experiment_no == run.experiment_no).first()
    experiment_name = experiment.experiment_name

    project_name = db.query(models.Project).filter(
        models.Project.project_id == experiment.project_id).first()
    project_name = project_name.project_name

    expdir = f'projects/{project_name}/{experiment_name}'
    dir = f'projects/{project_name}/{experiment_name}/runs/{run_name}'
    FILE = dir + '/runs_config.json'

    DATA = crud.create_run_config_file(
        db=db, model=model,expname=experiment_name ,runname=run_name, rundir = dir, expdir = expdir)

    DATA = json.dumps(DATA)
    _ = open(FILE, mode='w+').write(DATA)

    with open(FILE) as file:
        result = json.load(file)

    add_path = crud.update_run_config_path(
        run_no=run_no, db=db, dir=FILE)
    return "saved"

from fastapi import Request
@app.post("/client_registration", status_code=status.HTTP_200_OK)
async def add_new_client(request:Request,db: Session = Depends(get_db), ):
    
    
    form = await request.form()
    token = form["token"]
    port = form["port"]
    ipaddress = form["ipaddress"]
    client_name = form["client_name"]

    client_token = crud.get_tokens(db= db, token=token)
    if client_token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="token not found")
    
    # existing_token = crud.check_token(db= db, token=token)

    # if existing_token:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT, detail="token already registered")
    
    crud.add_client(db=db, client_name = client_name,token =token, port = port,ipaddress=ipaddress)
    



    exp =  crud.get_exp_by_token(db = db, token = token)
    path = exp.experiment_config_path
    file_path = f"{path}/archives.zip"
    return FileResponse(file_path)
    


@app.get("/get_clients/")
def get_clients_by_token(token: str, db: Session = Depends(get_db)):

    clients = db.query(models.Client).filter(
        models.Client.token == token).all()

    if clients is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no clients")

    
    return clients




if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)