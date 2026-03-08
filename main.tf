terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

# Tell Terraform how to talk to your K3s cluster
provider "kubernetes" {
  config_path = "/etc/rancher/k3s/k3s.yaml"
}

# 1. THE DEPLOYMENT: Keeps your container running
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
          image             = "smart-clinic:latest"
          name              = "smart-clinic"
          image_pull_policy = "Never" # Tells K8s to use the local image we just imported!
          
          port {
            container_port = 5000
          }
        }
      }
    }
  }
}

# 2. THE SERVICE: Opens the network port so you can see the app
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
      node_port   = 30050 # We are mapping K8s port to port 30050 on your home server
    }
    type = "NodePort"
  }
}