# Neuro-data-Project

## A Brief of the Problem statement

Create a web app application to perform Data cleaning, Feature engineering, and EDA.
The web application should allow the user to perform various data transformation
operations on the dataset with help of prebuild component. Users must be able to drag
and drop the existing component at UI to perform any operation.

## Application deployment link
https://autodataai.azurewebsites.net/
(Currently deactived)

## Demo video link
https://youtu.be/9ENomFFT5ZE

## Features

----- Main Page -----
1. Login and Authentication
2. Project Creation 
3. Data Ingestion (from Local, Database and Cloud)
4. DataFlows page with ETL components(like aggregate, merge-join, multicast etc) 

----- Data science Life Cycle ------
1. Exploratory Data Analysis
2. Data Preprocessing
3. Feature Engineering
4. Export section
5. Project Operations section
6. Custom script page
7. System Live Logs
8. Help page


## Dashboard Interface

![captures_chrome-capture-2023-2-1](https://user-images.githubusercontent.com/73020771/223081479-a1328711-f8e6-470e-96a7-df8005c8854f.png)


## Tech Stack

Framework:
Django

Front End: 
1. Html
2. Css
3. Javascript
4. Jquery
5. HTMX

Back End:
1. Python 3.9
2. Data Preprocessing Libs(Numpy, Pandas, Matplotlib, Plotly)
3. Database (MongoDB, Mysql, Sqlite3)
4. DataFlows Library for prebuilt components ![Dataflows Component python library](https://github.com/datahq/dataflows/blob/master/PROCESSORS.md)

## Deployment Architecture:
Azure web app service
![cs drawio (1)](https://user-images.githubusercontent.com/73020771/223089084-65e07610-0615-45b8-bcd9-e7df174eef97.png)


## Complete Documentation
https://drive.google.com/drive/folders/1rtgib-mMRg5fHhSu_uYNiUxPDOxqmesV?usp=sharing

## How to run the app locally?

### Step 1: Clone the repo
``` git clone https://github.com/Suhaib-88/Neuro-data-Project.git  ```
<br>
``` cd Neuro-data-Project  ```

### Step 2: Create virtual environment

``` conda create -n testenv python=3.9 -y ```
<br>
``` conda activate testenv ```

### Step 3: Install the required libraries

Using pip
``` pip install -r requirements.txt ```
<br>
or
<br>
``` python setup.py install ```

### Step 4: Run the app

``` python manage.py runserver ```

Alternatively you can build and run docker using:

docker build
``` docker build -t <IMAGE_NAME> ```

docker run
``` docker run -d -p 8080:8080 <IMAGE_NAME> ```

## Contributors
@Suhaib-88

## Support
For Any kind of queries or feedback mail me suhaibarshad2017@gmail.com
