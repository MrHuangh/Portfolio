<script>
	export default {
		onLaunch: function() {
			console.log('AI智能检测 App Launch');
		},
		onShow: function() {
			console.log('AI智能检测 App Show');
		},
		onHide: function() {
			console.log('AI智能检测 App Hide');
		}
	};
</script>

<style>
	/* 全局样式 */
	page {
		background-color: #0f0f23;
		color: #ffffff;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
	}
	
	/* 通用按钮样式 */
	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: #fff;
		border: none;
		border-radius: 12px;
		padding: 14rpx 40rpx;
		font-size: 32rpx;
		font-weight: 600;
		box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.35);
		transition: all 0.3s ease;
	}
	
	.btn-primary:active {
		transform: scale(0.96);
		box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.2);
	}
	
	/* 卡片样式 */
	.card {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 20rpx;
		backdrop-filter: blur(20px);
		-webkit-backdrop-filter: blur(20px);
	}
</style>
