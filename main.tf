terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

provider "kubernetes" {
  config_path = "/etc/rancher/k3s/k3s.yaml"
}

resource "kubernetes_deployment" "clinic_app" {
  metadata {
    name = "smart-clinic"
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "smart-clinic"
      }
    }
    template {
      metadata {
        labels = {
          app = "smart-clinic"
        }
      }
      spec {
        container {
          # ---> CHANGE THIS TO YOUR DOCKER HUB USERNAME <---
          image             = "YOUR_DOCKERHUB_USERNAME/smart-clinic:latest"
          name              = "smart-clinic"
          image_pull_policy = "Always" 
          
          port {
            container_port = 5000
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "clinic_service" {
  metadata {
    name = "smart-clinic-service"
  }
  spec {
    selector = {
      app = "smart-clinic"
    }
    port {
      port        = 5000
      target_port = 5000
      node_port   = 30050 
    }
    type = "NodePort"
  }
}