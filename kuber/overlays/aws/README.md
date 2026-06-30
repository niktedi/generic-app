# Placeholder for the future AWS environment.
#
# When you build this out, it will look roughly like the homelab overlay but with:
#   - storageclass.yaml      -> gp3 / ebs-sc (EBS CSI), OR drop postgres entirely
#                               and point the app at managed RDS
#   - service exposure       -> type: LoadBalancer (ELB) or an Ingress (ALB)
#   - secret strategy        -> a SealedSecret sealed by the AWS cluster's
#                               controller key, OR External Secrets + AWS
#                               Secrets Manager (no ArgoCD on AWS per the plan,
#                               so CI would `kustomize build overlays/aws | kubectl apply -f -`)
#   - migration Job          -> stays a plain Job (no ArgoCD hook annotations);
#                               CI runs it before applying, or it runs as-is
#
# Because storageClassName in a StatefulSet volumeClaimTemplate is immutable,
# the AWS overlay should REPLACE the base StatefulSet wholesale rather than
# patch its VCT.
