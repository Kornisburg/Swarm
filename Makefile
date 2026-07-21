REGISTRY ?= us-central1-docker.pkg.dev/$(PROJECT_ID)/hive
TAG ?= latest
PROJECT_ID ?= the-hive-project
REGION ?= us-central1
CLUSTER_NAME ?= hive-cluster

.PHONY: help build push deploy k8s-apply k8s-apply-manual terraform-apply terraform-destroy tf-init clean

help:
	@echo 'Available targets:'
	@echo '  build             Build Docker image'
	@echo '  push              Push image to Artifact Registry'
	@echo '  deploy            Full deploy: build + push + k8s-apply'
	@echo '  k8s-apply         Apply K8s manifests (use with Terraform-managed ConfigMap)'
	@echo '  k8s-apply-manual  Apply ALL manifests including ConfigMap + Secret (no Terraform)'
	@echo '  k8s-delete        Delete all Kubernetes resources'
	@echo '  tf-init           Initialize Terraform'
	@echo '  terraform-apply   Provision GCloud infrastructure'
	@echo '  terraform-destroy Tear down infrastructure'
	@echo ''
	@echo 'Variables:'
	@echo '  PROJECT_ID=$(PROJECT_ID)'
	@echo '  REGION=$(REGION)'
	@echo '  CLUSTER_NAME=$(CLUSTER_NAME)'
	@echo '  TAG=$(TAG)'

build:
	docker build -t $(REGISTRY)/hive:$(TAG) .

push: build
	docker tag $(REGISTRY)/hive:$(TAG) $(REGISTRY)/hive:$(TAG)
	docker push $(REGISTRY)/hive:$(TAG)

# Safe for both Terraform-managed and manual deployments.
# Skips ConfigMap + Secret to avoid overwriting Terraform-managed resources.
k8s-apply:
	kubectl apply -f infra/kubernetes/namespace.yaml
	kubectl apply -f infra/kubernetes/chroma-deployment.yaml
	kubectl apply -f infra/kubernetes/chroma-service.yaml
	kubectl apply -f infra/kubernetes/hive-deployment.yaml
	kubectl apply -f infra/kubernetes/hive-service.yaml
	kubectl apply -f infra/kubernetes/hive-ingress.yaml
	kubectl apply -f infra/kubernetes/hpa.yaml

# Applies ConfigMap + Secret too. Use when NOT using Terraform.
# WARNING: overwrites any Terraform-managed ConfigMap.
k8s-apply-manual: k8s-apply
	kubectl apply -f infra/kubernetes/configmap.yaml
	-kubectl create secret generic hive-secrets \
		--namespace=hive \
		--from-literal=postgres-password=$${POSTGRES_PASSWORD:-hive_password} \
		--from-literal=langchain-api-key=$${LANGCHAIN_API_KEY:-} \
		--from-literal=openai-api-key=$${OPENAI_API_KEY:-} \
		--from-literal=anthropic-api-key=$${ANTHROPIC_API_KEY:-} \
		--dry-run=client -o yaml | kubectl apply -f -

k8s-delete:
	-kubectl delete -f infra/kubernetes/ --ignore-not-found

deploy: push k8s-apply

tf-init:
	cd infra/terraform && terraform init

terraform-apply:
	cd infra/terraform && terraform apply

terraform-destroy:
	cd infra/terraform && terraform destroy

clean:
	-docker rmi $(REGISTRY)/hive:$(TAG) 2>/dev/null || true
