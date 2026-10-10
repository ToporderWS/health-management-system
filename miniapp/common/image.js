/**
 * 真机图片加载适配层。
 *
 * 背景：微信小程序在**真机**上会拦截 <image> 组件加载 http:// 网络图片 ——
 * 图片走的是系统图片通道，开发者工具里的「不校验合法域名」只放行 JSBridge 请求，
 * 官方文档也把图片归入「其他 HTTPS 请求」（https 的图片无法加载按证书流程排查）。
 * 表现就是：接口数据一切正常，只有图片位置空白（白色圆形）。
 *
 * 做法：对 http:// 地址先用 uni.downloadFile 下载到本地临时文件（与 wx.request
 * 同一条 JSBridge 通道，「不校验合法域名」开启时可访问局域网 IP），再用本地路径渲染。
 * https:// 地址与本地打包资源原样返回，不做任何额外处理，因此对生产环境零影响；
 * 若下载失败也仍回落到原始地址，行为与改造前完全一致。
 *
 * 数据库仍然只保存文件名，URL 前缀仍由 common/config.js 的 resolveFileUrl 负责。
 */
import { reactive } from 'vue'

import { resolveFileUrl } from './config'

/** 原始地址 -> 本地临时文件路径（响应式：下载完成后自动触发重新渲染） */
const localPaths = reactive({})
/** 正在下载的原始地址（非响应式，仅用于去重，避免重复请求） */
const inflight = {}
/** 已下载失败的原始地址（非响应式；避免每次重渲染都重复发起同一个失败请求） */
const failed = {}

/** 是否为明文 http 地址（只有这种地址在真机上会被 <image> 拦截） */
function isPlainHttp(url) {
  return typeof url === 'string' && url.slice(0, 7).toLowerCase() === 'http://'
}

/** 需要时把 http 地址本地化；下载完成前先返回原始地址占位 */
function localize(url) {
  if (!isPlainHttp(url)) return url

  const cached = localPaths[url]
  if (cached) return cached
  // 已在下载中 / 已失败过 —— 都不再重复发起请求，直接回落原始地址。
  // （渲染函数里读取 localPaths[url] 只建立依赖、不写响应式；写入只发生在异步回调里，
  //   因此不会出现 render → 改 reactive → render 的循环。）
  if (inflight[url] || failed[url]) return url
  if (typeof uni === 'undefined' || typeof uni.downloadFile !== 'function') return url

  inflight[url] = true
  uni.downloadFile({
    url,
    success: (res) => {
      if (res && res.statusCode === 200 && res.tempFilePath) {
        localPaths[url] = res.tempFilePath
      } else {
        failed[url] = true
      }
    },
    fail: () => {
      failed[url] = true
    },
    complete: () => {
      inflight[url] = false
    },
  })
  return url
}

/**
 * 页面统一使用的图片地址入口：传入数据库中保存的文件名，返回可直接给 <image> 的地址。
 */
export function imgSrc(filename) {
  return localize(resolveFileUrl(filename))
}
