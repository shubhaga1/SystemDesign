# Project - Build a Task Manager

## Features
	- Multiple users can use the app 
	- Every user can add tasks 
	- After creating a task, user can assign it to different user 
	- Tasks
		- has a description
		- priority: enum<high/low/medium>
		- has a due date
		- has a state: pending / completed 
		- Notes
			- A task can have multiple notes inside it
			- Notes can be made by the owner or asignee 
	- The creator of the task can edit / delete the task 
	- The creator or asignee can mark the task as done 


## DB Schema Design

base_table
- id  - 			integer autoincrement primary key
- created_at - 	date
- updated_at -	date
	

users
- name - string(100)
- email - string(100) : validate(email)

tasks
- description - string
- priority - enum[high,medium,low]
- due_date - date
- status   - enum[pending,completed]
- creator_id  - fk(users.id)
- asignee_id	- fk(users.id)

notes 
- task_id		- fk(tasks.id)
- description - string 
- author_id	- fk(users.id)

## REST API



| method 	| /resource<br><br><br>/students                                                                                                                        	| /resource/{id}<br><br><br>/students/44                                                                                                                                                                                                                                                                     	|
|--------	|-------------------------------------------------------------------------------------------------------------------------------------------------------	|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------	|
| GET    	| get data of all students in array format<br><br>eg: <br>RESP <- [{name, age,...}, {name, age,...}, ...]                                               	| get data of student #44 in object format<br><br>eg: <br>RESP <- {name: Deepika, company: IBM}                                                                                                                                                                                                              	|
| POST   	| create a new student (id will be generated by server)<br><br>eg:<br>BODY -> {name: Kishore, company: Scaler}<br>RESP <- {success: true, id: 55}       	| *generally not implemented*                                                                                                                                                                                                                                                                                	|
| PUT    	| *generally not implemented* <br>replace the **ENTIRE** collection with the given array <br><br>eg:<br>BODY -> [{name, age,...}, {name, age,...}, ...] 	| create new student with id 44, or replace <br>existing student with id = 44 <br><br>eg: <br>EXISTING: {name: Deepika, company: IBM}<br><br>BODY -> {name: Kishore, company: Scaler}<br>RESP <- {name: Kishore, company: Scaler}                                                                            	|
| PATCH  	| *generally not implemented*                                                                                                                           	| update student id = 44 with given data<br>i.e. <br>new keys are added <br>same keys are overwritten <br>missing keys remain as it is <br><br>eg:<br>EXISTING: {name: Deepika, company: IBM}<br><br>BODY -> {company: Scaler, city: Hyderabad}<br>RESP <- {name: Deepika, company: Scaler, city: Hyderabad} 	|
| DELETE 	| *generally not implemented* <br><br>delete all data in students collection                                                                            	| delete student with id = 44<br><br><br>RESP <- {success: true}                                                                                                                                                                                                                                             	|