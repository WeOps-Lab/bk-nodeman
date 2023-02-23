version ?= "dev"
image_repo ?= "mirrors.tencent.com/nodeman"
bkapp_run_env ?= "ee"
RELEASE_PATH=/opt/release/bk_nodeman
SERVER_PATH=/opt/release/bknodeman
VENV_PATH=/tmp/venv

build-family-bucket:
	docker build -f support-files/kubernetes/images/family_bucket/Dockerfile -t ${image_repo}/bk-nodeman:${version} --build-arg BKAPP_RUN_ENV=${bkapp_run_env} .

push-family-bucket:
	docker push ${image_repo}/bk-nodeman:${version}

release-ui:
	cd frontend/ && npm install  && npm run build

release-server:
	rm -Rf $(SERVER_PATH)
	mkdir -p $(SERVER_PATH)/nodeman

	cp -R ./apps $(SERVER_PATH)/nodeman
	cp -R ./bin $(SERVER_PATH)/nodeman
	cp -R ./blueking $(SERVER_PATH)/nodeman
	cp -R ./official_plugin $(SERVER_PATH)/nodeman
	cp -R ./bkoauth $(SERVER_PATH)/nodeman
	cp -R ./common $(SERVER_PATH)/nodeman
	cp -R ./locale $(SERVER_PATH)/nodeman
	cp -R ./pipeline $(SERVER_PATH)/nodeman
	cp -R ./version_log $(SERVER_PATH)/nodeman
	cp -R ./script_tools $(SERVER_PATH)/nodeman
	cp -R ./config $(SERVER_PATH)/nodeman
	cp -R ./upgrade $(SERVER_PATH)/nodeman
	cp -R ./env $(SERVER_PATH)/nodeman

	cp ./manage.py $(SERVER_PATH)/nodeman
	cp ./settings.py $(SERVER_PATH)/nodeman
	cp ./app.yml $(SERVER_PATH)/nodeman
	cp ./urls.py $(SERVER_PATH)/nodeman
	cp ./wsgi.py $(SERVER_PATH)/nodeman
	cp ./on_migrate $(SERVER_PATH)/nodeman
	cp ./requirements.txt $(SERVER_PATH)/nodeman
	cp ./VERSION $(SERVER_PATH)
	cp -R ./version_log $(SERVER_PATH)/nodeman
	cp -Rf ./VERSION $(SERVER_PATH)/nodeman
	cp -Rf ./release $(SERVER_PATH)/nodeman
	mkdir $(SERVER_PATH)/nodeman/version_logs_html
	cp -Rf ./projects.yaml $(SERVER_PATH)
	cp -Rf ./support-files $(SERVER_PATH)
	
	rm -Rf $(SERVER_PATH)/nodeman/config/local_settings.py
	
	virtualenv $(VENV_PATH) -p python3
	$(VENV_PATH)/bin/pip download -r $(SERVER_PATH)/nodeman/requirements.txt -d $(SERVER_PATH)/support-files/pkgs
	rm -Rf $(VENV_PATH)

release-saas:
	rm -Rf $(RELEASE_PATH)
	mkdir -p $(RELEASE_PATH)/src
	cp -Rf ../bk-nodeman/* $(RELEASE_PATH)/src

	mkdir $(RELEASE_PATH)/pkgs
	virtualenv $(VENV_PATH) -p python3
	$(VENV_PATH)/bin/pip download -r $(RELEASE_PATH)/src/requirements.txt -d $(RELEASE_PATH)/pkgs

	cp -Rf $(RELEASE_PATH)/src/bk_nodeman.png $(RELEASE_PATH)
	cp -Rf $(RELEASE_PATH)/src/app.yml $(RELEASE_PATH)

	rm -Rf $(RELEASE_PATH)/src/frontend/node_modules/
	rm -Rf $(VENV_PATH)
