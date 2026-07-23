<template>
	<view class="container">
		<!-- 头部区域 -->
		<view class="header">
			<view class="header-glow"></view>
			<text class="header-title">AI 智能检测</text>
			<text class="header-subtitle">基于 YOLOv11 深度学习模型</text>
		</view>

		<!-- 上传区域 -->
		<view class="upload-section">
			<view class="section-label">
				<text class="label-icon">📷</text>
				<text class="label-text">选择图片</text>
			</view>

			<!-- 图片预览 -->
			<view class="preview-area" @tap="chooseImage">
				<image v-if="imageUrl" :src="imageUrl" mode="aspectFill" class="preview-image"></image>
				<view v-else class="placeholder">
					<view class="placeholder-icon">
						<text class="icon-text">+</text>
					</view>
					<text class="placeholder-text">点击选择图片</text>
					<text class="placeholder-hint">支持 JPG / PNG 格式</text>
				</view>
				<!-- 重新选择按钮 -->
				<view v-if="imageUrl" class="change-btn" @tap.stop="chooseImage">
					<text class="change-btn-text">重新选择</text>
				</view>
			</view>

			<!-- 操作按钮组 -->
			<view class="action-row">
				<view class="action-btn album-btn" @tap="chooseAlbum">
					<text class="action-icon">🖼</text>
					<text class="action-text">相册</text>
				</view>
				<view class="action-btn camera-btn" @tap="chooseCamera">
					<text class="action-icon">📸</text>
					<text class="action-text">拍照</text>
				</view>
			</view>
		</view>

		<!-- 检测按钮 -->
		<view class="detect-section">
			<button
				class="detect-btn"
				:class="{ 'btn-disabled': !imageUrl || loading }"
				:disabled="!imageUrl || loading"
				@tap="startDetect"
			>
				<view v-if="loading" class="loading-wrapper">
					<view class="loading-spinner"></view>
					<text class="btn-text">AI 检测中...</text>
				</view>
				<view v-else class="btn-content">
					<text class="btn-icon">🔍</text>
					<text class="btn-text">开始检测</text>
				</view>
			</button>
		</view>

		<!-- 底部信息 -->
		<view class="footer">
			<view class="footer-item">
				<text class="footer-dot"></text>
				<text class="footer-text">支持口罩检测 / 工业缺陷检测</text>
			</view>
			<view class="footer-item">
				<text class="footer-dot"></text>
				<text class="footer-text">实时 AI 推理，秒级返回结果</text>
			</view>
		</view>

		<!-- 错误提示 -->
		<uni-popup ref="popup" type="center">
			<view class="error-card">
				<text class="error-icon">⚠️</text>
				<text class="error-title">检测失败</text>
				<text class="error-message">{{ errorMessage }}</text>
				<view class="error-btn" @tap="closeError">知道了</view>
			</view>
		</uni-popup>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				imageUrl: '',
				tempFilePath: '',
				loading: false,
				errorMessage: '',
				// Flask后端地址 - 根据实际地址修改
				baseUrl: 'http://localhost:5000'
			}
		},
		methods: {
			// 选择图片（弹窗选择来源）
			chooseImage() {
				uni.showActionSheet({
					itemList: ['相册选择', '拍照'],
					success: (res) => {
						if (res.tapIndex === 0) {
							this.chooseAlbum()
						} else {
							this.chooseCamera()
						}
					}
				})
			},

			// 从相册选择
			chooseAlbum() {
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					sourceType: ['album'],
					success: (res) => {
						this.tempFilePath = res.tempFilePaths[0]
						this.imageUrl = res.tempFilePaths[0]
					},
					fail: (err) => {
						if (err.errMsg !== 'chooseImage:fail cancel') {
							uni.showToast({
								title: '选择图片失败',
								icon: 'none'
							})
						}
					}
				})
			},

			// 拍照
			chooseCamera() {
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					sourceType: ['camera'],
					success: (res) => {
						this.tempFilePath = res.tempFilePaths[0]
						this.imageUrl = res.tempFilePaths[0]
					},
					fail: (err) => {
						if (err.errMsg !== 'chooseImage:fail cancel') {
							uni.showToast({
								title: '拍照失败',
								icon: 'none'
							})
						}
					}
				})
			},

			// 开始检测
			startDetect() {
				if (!this.imageUrl || this.loading) return

				this.loading = true

				uni.showLoading({
					title: 'AI检测中...',
					mask: true
				})

				uni.uploadFile({
					url: `${this.baseUrl}/ai_detect`,
					filePath: this.tempFilePath,
					name: 'my_img',
					success: (res) => {
						uni.hideLoading()
						this.loading = false

						if (res.statusCode === 200) {
							// 后端返回的是图片URL字符串
							const resultUrl = res.data
							// 跳转到结果页面
							uni.navigateTo({
								url: `/pages/result/result?imageUrl=${encodeURIComponent(resultUrl)}&originalImage=${encodeURIComponent(this.imageUrl)}`
							})
						} else {
							this.showError('服务器返回异常，请稍后重试')
						}
					},
					fail: (err) => {
						uni.hideLoading()
						this.loading = false

						if (err.errMsg.indexOf('timeout') > -1) {
							this.showError('请求超时，请检查网络连接或稍后重试')
						} else if (err.errMsg.indexOf('not connect') > -1 || err.errMsg.indexOf('fail') > -1) {
							this.showError('无法连接到服务器，请确保后端服务已启动')
						} else {
							this.showError('网络请求失败：' + err.errMsg)
						}
					}
				})
			},

			// 显示错误
			showError(msg) {
				this.errorMessage = msg
				this.$refs.popup.open()
			},

			// 关闭错误
			closeError() {
				this.$refs.popup.close()
			}
		}
	}
</script>

<style>
	.container {
		min-height: 100vh;
		padding: 30rpx;
		background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
	}

	/* ===== 头部 ===== */
	.header {
		position: relative;
		padding: 40rpx 20rpx 50rpx;
		text-align: center;
		overflow: hidden;
	}

	.header-glow {
		position: absolute;
		top: -100rpx;
		left: 50%;
		transform: translateX(-50%);
		width: 500rpx;
		height: 500rpx;
		background: radial-gradient(circle, rgba(102, 126, 234, 0.15) 0%, transparent 70%);
		pointer-events: none;
	}

	.header-title {
		font-size: 48rpx;
		font-weight: 700;
		color: #ffffff;
		letter-spacing: 4rpx;
		text-shadow: 0 0 40rpx rgba(102, 126, 234, 0.3);
		position: relative;
		z-index: 1;
	}

	.header-subtitle {
		display: block;
		margin-top: 12rpx;
		font-size: 26rpx;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 2rpx;
		position: relative;
		z-index: 1;
	}

	/* ===== 上传区域 ===== */
	.upload-section {
		margin-top: 20rpx;
	}

	.section-label {
		display: flex;
		align-items: center;
		margin-bottom: 24rpx;
	}

	.label-icon {
		font-size: 36rpx;
		margin-right: 12rpx;
	}

	.label-text {
		font-size: 32rpx;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
	}

	/* 预览区域 */
	.preview-area {
		position: relative;
		width: 100%;
		height: 480rpx;
		border-radius: 24rpx;
		overflow: hidden;
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 2rpx dashed rgba(255, 255, 255, 0.15);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
	}

	.preview-area:active {
		transform: scale(0.98);
		border-color: rgba(102, 126, 234, 0.4);
	}

	.preview-image {
		width: 100%;
		height: 100%;
	}

	/* 占位符 */
	.placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.placeholder-icon {
		width: 120rpx;
		height: 120rpx;
		border-radius: 50%;
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 24rpx;
		border: 2rpx solid rgba(102, 126, 234, 0.3);
	}

	.icon-text {
		font-size: 60rpx;
		color: rgba(102, 126, 234, 0.6);
		font-weight: 300;
		line-height: 1;
	}

	.placeholder-text {
		font-size: 30rpx;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}

	.placeholder-hint {
		font-size: 24rpx;
		color: rgba(255, 255, 255, 0.3);
		margin-top: 8rpx;
	}

	/* 重新选择按钮 */
	.change-btn {
		position: absolute;
		top: 16rpx;
		right: 16rpx;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		padding: 8rpx 20rpx;
		border-radius: 20rpx;
		border: 1rpx solid rgba(255, 255, 255, 0.15);
	}

	.change-btn-text {
		font-size: 22rpx;
		color: rgba(255, 255, 255, 0.8);
	}

	/* ===== 操作按钮组 ===== */
	.action-row {
		display: flex;
		gap: 20rpx;
		margin-top: 24rpx;
	}

	.action-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24rpx;
		border-radius: 16rpx;
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
		border: 1rpx solid rgba(255, 255, 255, 0.08);
		transition: all 0.3s ease;
	}

	.action-btn:active {
		transform: scale(0.96);
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.05) 100%);
	}

	.action-icon {
		font-size: 40rpx;
		margin-right: 12rpx;
	}

	.action-text {
		font-size: 28rpx;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 500;
	}

	/* ===== 检测按钮 ===== */
	.detect-section {
		margin-top: 40rpx;
		padding: 0 20rpx;
	}

	.detect-btn {
		width: 100%;
		height: 100rpx;
		line-height: 100rpx;
		text-align: center;
		border-radius: 50rpx;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		border: none;
		box-shadow: 0 12rpx 40rpx rgba(102, 126, 234, 0.35);
		transition: all 0.3s ease;
	}

	.detect-btn:active {
		transform: scale(0.96);
		box-shadow: 0 6rpx 20rpx rgba(102, 126, 234, 0.2);
	}

	.btn-disabled {
		opacity: 0.4;
		box-shadow: none !important;
	}

	.btn-content,
	.loading-wrapper {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
	}

	.btn-icon {
		font-size: 36rpx;
		margin-right: 12rpx;
	}

	.btn-text {
		font-size: 34rpx;
		color: #ffffff;
		font-weight: 600;
		letter-spacing: 4rpx;
	}

	/* 加载动画 */
	.loading-spinner {
		width: 36rpx;
		height: 36rpx;
		border: 4rpx solid rgba(255, 255, 255, 0.3);
		border-top-color: #ffffff;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin-right: 16rpx;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* ===== 底部信息 ===== */
	.footer {
		margin-top: 60rpx;
		padding: 0 20rpx;
	}

	.footer-item {
		display: flex;
		align-items: center;
		margin-bottom: 16rpx;
	}

	.footer-dot {
		width: 8rpx;
		height: 8rpx;
		border-radius: 50%;
		background: linear-gradient(135deg, #667eea, #764ba2);
		margin-right: 16rpx;
		flex-shrink: 0;
	}

	.footer-text {
		font-size: 24rpx;
		color: rgba(255, 255, 255, 0.3);
	}

	/* ===== 错误弹窗 ===== */
	.error-card {
		width: 560rpx;
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
		border-radius: 32rpx;
		padding: 50rpx 40rpx;
		text-align: center;
		border: 1rpx solid rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(20px);
		-webkit-backdrop-filter: blur(20px);
	}

	.error-icon {
		font-size: 72rpx;
		margin-bottom: 20rpx;
		display: block;
	}

	.error-title {
		font-size: 36rpx;
		font-weight: 700;
		color: #ffffff;
		margin-bottom: 16rpx;
		display: block;
	}

	.error-message {
		font-size: 28rpx;
		color: rgba(255, 255, 255, 0.6);
		line-height: 1.6;
		margin-bottom: 32rpx;
		display: block;
	}

	.error-btn {
		display: inline-block;
		padding: 16rpx 60rpx;
		border-radius: 40rpx;
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: #ffffff;
		font-size: 28rpx;
		font-weight: 600;
	}

	.error-btn:active {
		transform: scale(0.96);
	}
</style>
