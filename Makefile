# Copyright 2017 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.PHONY:	build push dev

PREFIX = hub.bccvl.org.au/ecocloud
IMAGE = tokenstore
TAG ?= 0.1.0

build:
	docker build -t $(PREFIX)/$(IMAGE):$(TAG) .

dev:
	docker run --rm -it -p 6543:6543 -v $(PWD):/tokenstore tokenstore $(PREFIX)/$(IMAGE):$(TAG) bash

migrate:
	docker run --rm -it -v $(PWD):/tokenstore tokenstore $(PREFIX)/$(IMAGE):$(TAG) alembic -c /tokenstore/development.ini upgrade head

push:
	docker push $(PREFIX)/$(IMAGE):$(TAG)
