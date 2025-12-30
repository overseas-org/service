

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS

from mysql_database import Database
from variables import db_creds
from serviceMap.positions import get_position
from serviceMap.positions import get_position, update_positions, create_position
from serviceMap.service_connection import create_services_connection, get_projects_connection, delete_services_connection, get_connection

import service.service as service



app = Flask(__name__)

CORS(app, supports_credentials=True)

bp = Blueprint('service', __name__,
                        template_folder='templates')


@bp.route("/service", methods=["POST"])
def create_service():
	data = request.json
	task_id = service.create_service(data)
	return jsonify({"task_id": task_id}), 200

@bp.route("/services", methods=["GET"])
def get_services():
	filter = request.args.get("filter", "")
	project_id = request.args.get("project_id")
	services = service.get_services(project_id, filter)
	return jsonify(services), 200

@bp.route("/service", methods=["GET"])
def get_service():
	filter = request.args.get("filter", "")
	# project_id = request.args.get("project_id")
	service_id = request.args.get("id")
	_service = service.get_service(service_id)
	return jsonify(_service), 200

@bp.route("/service", methods=["DELETE"])
def delete_service():
	service_id = request.args.get("id")
	task_id = service.delete_service(service_id)
	return jsonify({"task_id": task_id}), 200

@bp.route("/configure_service_connections", methods=["POST"])
def configure_service_connections():
	service_id = request.args.get("id")
	data = request.json
	service.configure_service_connections(service_id, data["connections"])
	return jsonify({"message": f"successfully updated service security network"}), 200


##########repo

@bp.route("/repo", methods=["GET"])
def get_repo():
	# project_id = request.args.get("project_id")
	repo_id = request.args.get("repo_id")
	repo_type = request.args.get("repo_type")
	db = Database("Repo", db_creds)
	obj = db.get_object_by_id(repo_type, repo_id, as_dict=True)
	return jsonify(obj), 200

@bp.route("/registry", methods=["GET"])
def get_registry():
	# project_id = request.args.get("project_id")
	registry_id = request.args.get("registry_id")
	registry_type = request.args.get("registry_type")
	db = Database("ImageRegistry", db_creds)
	obj = db.get_object_by_id(registry_type, registry_id, as_dict=True)
	return jsonify(obj), 200

@bp.route("/pipeline", methods=["GET"])
def get_pipeline():
	# project_id = request.args.get("project_id")
	pipeline_id = request.args.get("pipeline_id")
	pipeline_type = request.args.get("pipeline_type")
	db = Database("Pipeline", db_creds)
	obj = db.get_object_by_id(pipeline_type, pipeline_id, as_dict=True)
	return jsonify(obj), 200

@bp.route("/endpoints", methods=["GET"])
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

@bp.route("/positions", methods=["GET"])
def get_project_positions():
	project_id = request.args.get("project_id")
	positions = get_position(project_id)
	return jsonify(positions), 200

@bp.route("/positions", methods=["PUT"])
def update_project_positions():
	data = request.json
	update_positions(data["positions"])
	return jsonify({"message": "postions saved"}), 201

@bp.route("/position", methods=["POST"])
def create_project_position():
	data = request.json
	project_id = data["project_id"]
	service_id = data["service_id"]
	position_id = create_position(project_id, service_id)
	return jsonify({"position_id": position_id}), 201

@bp.route("/connection", methods=["POST"])
def create_connection():
	connection = request.json
	connection_id = create_services_connection(connection)
	connection = get_connection(connection_id)
	return jsonify(connection), 201

@bp.route("/connection", methods=["DELETE"])
def delete_connection():
	connection_id = request.args.get("connection_id")
	delete_services_connection(connection_id)
	return jsonify({"message": "connection saved"}), 204

@bp.route("/connections", methods=["GET"])
def get_connections():
	project_id = request.args.get("project_id")
	connections = get_projects_connection(project_id)
	return jsonify(connections), 200

app.register_blueprint(bp, url_prefix="/api/service")

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)
