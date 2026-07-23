<template>
	<view class="container">
		<!-- 对比展示 -->
		<view class="compare-section">
			<view class="section-label">
				<text class="label-icon">📊</text>
				<text class="label-text">检测结果</text>
			</view>

			<!-- 标签切换 -->
			<view class="tab-bar">
				<view
					class="tab-item"
					:class="{ 'tab-active': activeTab === 'result' }"
					@tap="activeTab = 'result'"
				>
					<text class="tab-text">检测结果</text>
				</view>
				<view
					class="tab-item"
					:class="{ 'tab-active': activeTab === 'original' }"
					@tap="activeTab = 'original'"
				>
					<text class="tab-text">原始图片</text>
				</view>
			</view>

			<!-- 图片展示 -->
			<view class="result-image-wrapper">
				<image
					v-if="activeTab === 'result' && resultImageUrl"
					:src="resultImageUrl"
					mode="widthFix"
					class="result-image"
					@tap="previewImage(resultImageUrl)"
				></image>
				<image
					v-else-if="activeTab === 'original' && originalImage"
					:src="originalImage"
					mode="widthFix"
					class="result-image"
					@tap="previewImage(originalImage)"
				></image>
				<view v-else class="image-placeholder">
					<text class="placeholder-emoji">🖼</text>
					<text class="placeholder-text">加载中...</text>
				</view>

				<!-- 图片操作提示 -->
				<view class="image-hint">
					<text class="hint-text">点击图片可查看大图</text>
				</view>
			</view>
		</view>

		<!-- 检测信息卡片 -->
		<view class="info-card">
			<view class="info-header">
				<text class="info-title">检测概览</text>
				<view class="info-badge">
					<text class="badge-text">YOLOv11</text>
				</view>
			</view>

			<view class="info-row">
				<text class="info-label">检测状态</text>
				<text class="info-value status-success">✓ 检测完成</text>
			</view>
			<view class="info-row">
				<text class="info-label">检测时间</text>
				<text class="info-value">{{ currentTime }}</text>
			</view>
			<view class="info-row">
				<text class="info-label">模型类型</text>
				<text class="info-value">YOLOv11 Nano</text>
			</view>
		</view>

		<!-- 操作按钮 -->
		<view class="action-section">
			<button class="action-btn primary-btn" @tap="goBack">
				<text class="action-btn-text">继续检测</text>
			</button>
			<button class="action-btn secondary-btn" @tap="saveImage">
				<text class="action-btn-text-secondary">保存图片</text>
			</button>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				resultImageUrl: '',
				originalImage: '',
				activeTab: 'result',
				currentTime: ''
			}
		},
		onLoad(options) {
			if (options.imageUrl) {
				this.resultImageUrl = decodeURIComponent(options.imageUrl)
			}
			if (options.originalImage) {
				this.originalImage = decodeURIComponent(options.originalImage)
			}
			this.currentTime = this.getCurrentTime()
		},
		methods: {
			getCurrentTime() {
				const now = new Date()
				const h = String(now.getHours()).padStart(2, '0')
				const m = String(now.getMinutes()).padStart(2, '0')
				const s = String(now.getSeconds()).padStart(2, '0')
				return `${h}:${m}:${s}`
			},

			// 预览图片
			previewImage(url) {
				uni.previewImage({
					urls: [url],
					current: url
				})
			},

			// 返回首页
			goBack() {
				uni.navigateBack()
			},

			// 保存图片到相册
			saveImage() {
				const url = this.activeTab === 'result' ? this.resultImageUrl : this.originalImage
				if (!url) return

				uni.showLoading({
					title: '保存中...',
					mask: true
				})

				// 先下载图片到本地
				uni.downloadFile({
					url: url,
					success: (res) => {
						if (res.statusCode === 200) {
							uni.saveImageToPhotosAlbum({
								filePath: res.tempFilePath,
								success: () => {
									uni.hideLoading()
									uni.showToast({
										title: '保存成功',
										icon: 'success'
									})
								},
								fail: () => {
									uni.hideLoading()
									uni.showToast({
										title: '保存失败，请检查相册权限',
										icon: 'none'
									})
								}
							})
						} else {
							uni.hideLoading()
							uni.showToast({
								title: '下载图片失败',
								icon: 'none'
							})
						}
					},
					fail: () => {
						uni.hideLoading()
						uni.showToast({
							title: '网络错误',
							icon: 'none'
						})
					}
				})
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

	/* ===== 对比区域 ===== */
	.compare-section {
		margin-bottom: 30rpx;
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

	/* ===== Tab切换 ===== */
	.tab-bar {
		display: flex;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 16rpx;
		padding: 6rpx;
		margin-bottom: 24rpx;
	}

	.tab-item {
		flex: 1;
		text-align: center;
		padding: 16rpx 0;
		border-radius: 12rpx;
		transition: all 0.3s ease;
	}

	.tab-active {
		background: linear-gradient(135deg, #667eea, #764ba2);
		box-shadow: 0 4rpx 16rpx rgba(102, 126, 234, 0.3);
	}

	.tab-text {
		font-size: 28rpx;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}

	.tab-active .tab-text {
		color: #ffffff;
		font-weight: 600;
	}

	/* ===== 图片展示 ===== */
	.result-image-wrapper {
		position: relative;
		width: 100%;
		border-radius: 24rpx;
		overflow: hidden;
		background: rgba(0, 0, 0, 0.3);
		border: 1rpx solid rgba(255, 255, 255, 0.08);
	}

	.result-image {
		width: 100%;
		display: block;
	}

	.image-placeholder {
		width: 100%;
		height: 400rpx;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.placeholder-emoji {
		font-size: 64rpx;
		margin-bottom: 16rpx;
	}

	.placeholder-text {
		font-size: 28rpx;
		color: rgba(255, 255, 255, 0.4);
	}

	.image-hint {
		position: absolute;
		bottom: 16rpx;
		left: 50%;
		transform: translateX(-50%);
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		padding: 6rpx 24rpx;
		border-radius: 20rpx;
	}

	.hint-text {
		font-size: 22rpx;
		color: rgba(255, 255, 255, 0.5);
	}

	/* ===== 信息卡片 ===== */
	.info-card {
		margin-top: 20rpx;
		padding: 32rpx;
		border-radius: 24rpx;
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 1rpx solid rgba(255, 255, 255, 0.08);
	}

	.info-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 24rpx;
		padding-bottom: 20rpx;
		border-bottom: 1rpx solid rgba(255, 255, 255, 0.06);
	}

	.info-title {
		font-size: 30rpx;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
	}

	.info-badge {
		padding: 6rpx 20rpx;
		border-radius: 20rpx;
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
		border: 1rpx solid rgba(102, 126, 234, 0.3);
	}

	.badge-text {
		font-size: 22rpx;
		color: rgba(102, 126, 234, 0.9);
		font-weight: 600;
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 14rpx 0;
	}

	.info-label {
		font-size: 28rpx;
		color: rgba(255, 255, 255, 0.5);
	}

	.info-value {
		font-size: 28rpx;
		color: rgba(255, 255, 255, 0.85);
		font-weight: 500;
	}

	.status-success {
		color: #2ed573;
	}

	/* ===== 操作按钮 ===== */
	.action-section {
		margin-top: 40rpx;
		display: flex;
		flex-direction: column;
		gap: 20rpx;
	}

	.action-btn {
		width: 100%;
		height: 90rpx;
		line-height: 90rpx;
		text-align: center;
		border-radius: 50rpx;
		border: none;
		transition: all 0.3s ease;
	}

	.action-btn:active {
		transform: scale(0.96);
	}

	.primary-btn {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		box-shadow: 0 8rpx 32rpx rgba(102, 126, 234, 0.3);
	}

	.secondary-btn {
		background: rgba(255, 255, 255, 0.06);
		border: 1rpx solid rgba(255, 255, 255, 0.12);
	}

	.action-btn-text {
		font-size: 32rpx;
		color: #ffffff;
		font-weight: 600;
		letter-spacing: 4rpx;
	}

	.action-btn-text-secondary {
		font-size: 30rpx;
		color: rgba(255, 255, 255, 0.7);
		font-weight: 500;
	}
</style>
