# 在 Proxmox（pve 730A）準備 Ubuntu 24.04 VM

這份給助教 / 講師。學生如果是自己開 VM，直接跳到 [學生自己裝](#學生自己裝)。

建議規格：**2 vCPU / 4 GB RAM / 20 GB 磁碟**（六個模組全開約用 1.5 GB RAM）。

## 1. 建立 Ubuntu 24.04 cloud-init 範本（只要做一次）

在 PVE 節點的 shell（Web UI → 730A → Shell）執行。`9000`、`local-lvm`、`vmbr0` 請依你的環境調整。

```bash
cd /var/lib/vz/template/iso
wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img

qm create 9000 --name ubuntu-2404-tpl --memory 4096 --cores 2 \
  --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-pci \
  --agent enabled=1 --ostype l26
qm set 9000 --scsi0 local-lvm:0,import-from=/var/lib/vz/template/iso/noble-server-cloudimg-amd64.img
qm resize 9000 scsi0 20G
qm set 9000 --ide2 local-lvm:cloudinit --boot order=scsi0 --serial0 socket --vga serial0
qm set 9000 --ciuser student --sshkeys ~/.ssh/authorized_keys --ipconfig0 ip=dhcp
qm template 9000
```

## 2.（建議）做一個「已裝好 Docker、已拉好 image」的 golden 範本

教室裡 30 台 VM 通常共用同一個對外 IP，同時去 Docker Hub 拉 image
很容易撞到匿名下載次數限制（429 Too Many Requests）。先在範本裡拉好，上課就不用等。

```bash
qm clone 9000 9001 --name o11y-lab-golden --full
qm start 9001
# 進 VM 之後：
git clone https://github.com/Hikana/LSA-mon-o11y-class.git
cd LSA-mon-o11y-class
sudo ./scripts/setup-ubuntu.sh --pull
sudo cloud-init clean && sudo truncate -s 0 /etc/machine-id && sudo poweroff
# 回到 PVE：
qm template 9001
```

## 3. 幫每位學生開一台

```bash
for i in $(seq 1 30); do
  id=$((100 + i))
  qm clone 9001 $id --name o11y-s$(printf %02d $i) --full
  qm start $id
done
```

如果要讓學生的瀏覽器連到 VM 上的 Grafana（3000）、Prometheus（9090）等埠，
確認 `vmbr0` 和學生電腦在同一個網段，或用 SSH port forward：

```bash
ssh -L 3000:localhost:3000 -L 9090:localhost:9090 -L 8000:localhost:8000 student@<VM-IP>
```

## 學生自己裝

在自己的 Ubuntu 24.04 VM 裡：

```bash
git clone https://github.com/Hikana/LSA-mon-o11y-class.git
cd LSA-mon-o11y-class
sudo ./scripts/setup-ubuntu.sh
newgrp docker        # 或登出再登入
./lab.sh up 01
```

## Lab 用到的埠

| 埠 | 服務 | 模組 |
|---|---|---|
| 8000 | 加選系統 | 01 |
| 9100 | node_exporter | 02 |
| 9090 | Prometheus | 04 |
| 3000 | Grafana（admin / admin） | 05 |
| 9093 | Alertmanager | 06 |
