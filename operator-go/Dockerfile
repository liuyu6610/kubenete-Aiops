# ── 构建阶段 ──
FROM golang:1.21-alpine AS builder

WORKDIR /workspace

# 缓存依赖
COPY go.mod ./
# COPY go.sum ./
# RUN go mod download

# 复制源码
COPY cmd/ cmd/
# COPY api/ api/
# COPY controllers/ controllers/

# 构建二进制文件
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -a -o manager cmd/main.go

# ── 运行阶段 ──
FROM alpine:3.18
WORKDIR /

# 安装必要的系统证书等
RUN apk add --no-cache ca-certificates tzdata

COPY --from=builder /workspace/manager .

# 使用非 root 用户运行
USER 65532:65532

ENTRYPOINT ["/manager"]
