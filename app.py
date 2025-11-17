

from flask import Flask, request, jsonify
from flask_cors import CORS

from mysql_database import Database
from variables import db_creds
from serviceMap.positions import get_position
from serviceMap.positions import get_position, update_positions, create_positions
from serviceMap.service_connection import create_services_connection, get_projects_connection

import service.service as service



app = Flask(__name__)

CORS(app, supports_credentials=True)


@app.route("/service", methods=["POST"])
def create_service():
	data = request.json
	service_id = service.create_service(data)
	return jsonify({"service_id": service_id}), 200

@app.route("/services", methods=["GET"])
def get_services():
	filter = request.args.get("filter", "")
	project_id = request.args.get("project_id")
	services = service.get_services(project_id, filter)
	return jsonify(services), 200

@app.route("/service", methods=["GET"])
def get_service():
	filter = request.args.get("filter", "")
	# project_id = request.args.get("project_id")
	service_id = request.args.get("id")
	_service = service.get_service(service_id)
	return jsonify(_service), 200

@app.route("/service", methods=["DELETE"])
def delete_service():
	service_id = request.args.get("id")
	service.delete_service(service_id)
	return jsonify({"message": f"successfully deleted service with id:{service_id}"}), 204


##########repo

@app.route("/repo", methods=["GET"])
def get_repo():
	# project_id = request.args.get("project_id")
	repo_id = request.args.get("repo_id")
	repo_type = request.args.get("repo_type")
	db = Database("Repo", db_creds)
	obj = db.get_object_by_id(repo_type, repo_id, as_dict=True)
	return jsonify(obj), 200

@app.route("/registry", methods=["GET"])
def get_registry():
	# project_id = request.args.get("project_id")
	registry_id = request.args.get("registry_id")
	registry_type = request.args.get("registry_type")
	db = Database("ImageRegistry", db_creds)
	obj = db.get_object_by_id(registry_type, registry_id, as_dict=True)
	return jsonify(obj), 200

@app.route("/pipeline", methods=["GET"])
def get_pipeline():
	# project_id = request.args.get("project_id")
	pipeline_id = request.args.get("pipeline_id")
	pipeline_type = request.args.get("pipeline_type")
	db = Database("Pipeline", db_creds)
	obj = db.get_object_by_id(pipeline_type, pipeline_id, as_dict=True)
	return jsonify(obj), 200

@app.route("/endpoints", methods=["GET"])
def get_endpoints():
	# project_id = request.args.get("project_id")
	service_id = request.args.get("service_id")
	db = Database("Endpoints", db_creds)
	endpoints = db.get_list_of_objects("Endpoint", {"service_id": service_id})
	results = []
	for endpoint in endpoints:
		results.append(db.get_object_by_id(endpoint.endpoint_type, endpoint.endpoint_id, as_dict=True))

	return jsonify(results), 200

############ map

@app.route("/positions", methods=["GET"])
def get_project_positions():
	project_id = request.args.get("project_id")
	positions = get_position(project_id)
	return jsonify(positions), 200

@app.route("/positions", methods=["PUT"])
def update_project_positions():
	data = request.json
	update_positions(data["positions"])
	return jsonify({"message": "postions saved"}), 201

@app.route("/position", methods=["POST"])
def create_project_position():
	data = request.json
	project_id = data["project_id"]
	service_id = data["service_id"]
	create_positions(project_id, service_id)
	return jsonify({"message": "postions saved"}), 201

@app.route("/connection", methods=["POST"])
def create_connection():
	data = request.json
	create_services_connection(data)
	return jsonify({"message": "connection saved"}), 201

@app.route("/connections", methods=["GET"])
def get_connection():
	project_id = request.args.get("project_id")
	connections = get_projects_connection(project_id)
	return jsonify(connections), 200

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)