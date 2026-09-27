<script setup lang="ts">
/**
 * 外链入口。
 *
 * 这就是"留的口子"：新增一个平台入口不需要改前端代码，
 * 有管理权限的人直接在页面上添加即可（也可在 Django 后台操作）。
 */

import { Dialog, Notify } from 'quasar'
import { computed, onMounted, ref } from 'vue'

import {
  createExternalLink,
  fetchExternalLinks,
  removeExternalLink,
  updateExternalLink,
} from '@/shared/api/portal'
import type { ExternalLink, Paginated } from '@/shared/types'
import { useAuthStore } from '@/shell/auth'

const auth = useAuthStore()

const links = ref<ExternalLink[]>([])
const loading = ref(false)

/** 是否可管理（决定是否显示新增/编辑/删除按钮） */
const canManage = computed(() => auth.hasPerm('portal.links.manage'))

/** 按分组聚合，保持后端返回的排序 */
const grouped = computed(() => {
  const map = new Map<string, ExternalLink[]>()
  for (const item of links.value) {
    const key = item.category || '未分组'
    const bucket = map.get(key)
    if (bucket) {
      bucket.push(item)
    } else {
      map.set(key, [item])
    }
  }
  return [...map.entries()].map(([category, items]) => ({ category, items }))
})

// ─────────────────────────────────────────── 对话框

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const ICON_OPTIONS = [
  'link',
  'business',
  'school',
  'restaurant',
  'inventory_2',
  'cloud',
  'chat',
  'description',
  'assessment',
  'dashboard',
  'menu_book',
  'support_agent',
]

const form = ref({
  title: '',
  url: '',
  icon: 'link',
  description: '',
  category: '常用入口',
  order: 100,
  is_active: true,
  open_in_new_tab: true,
  required_perm: 'portal.links.view',
})

function resetForm(): void {
  form.value = {
    title: '',
    url: '',
    icon: 'link',
    description: '',
    category: '常用入口',
    order: 100,
    is_active: true,
    open_in_new_tab: true,
    required_perm: 'portal.links.view',
  }
}

function openCreate(): void {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(item: ExternalLink): void {
  editingId.value = item.id
  form.value = {
    title: item.title,
    url: item.url,
    icon: item.icon || 'link',
    description: item.description,
    category: item.category || '常用入口',
    order: item.order,
    is_active: item.is_active,
    open_in_new_tab: item.open_in_new_tab,
    required_perm: item.required_perm,
  }
  dialogVisible.value = true
}

async function save(): Promise<void> {
  saving.value = true
  try {
    if (editingId.value === null) {
      await createExternalLink({ ...form.value })
      Notify.create({ type: 'positive', message: '入口已添加', position: 'top' })
    } else {
      await updateExternalLink(editingId.value, { ...form.value })
      Notify.create({ type: 'positive', message: '入口已更新', position: 'top' })
    }
    dialogVisible.value = false
    await load()
  } catch {
    // 统一错误提示由 http 层处理
  } finally {
    saving.value = false
  }
}

async function remove(item: ExternalLink): Promise<void> {
  const confirmed = await new Promise<boolean>((resolve) => {
    Dialog.create({
      title: '删除确认',
      message: `确定要删除入口「${item.title}」吗？此操作不可撤销。`,
      cancel: { label: '取消', flat: true },
      ok: { label: '删除', color: 'negative', unelevated: true },
      persistent: true,
    })
      .onOk(() => resolve(true))
      .onCancel(() => resolve(false))
      .onDismiss(() => resolve(false))
  })
  if (!confirmed) return

  try {
    await removeExternalLink(item.id)
    Notify.create({ type: 'positive', message: `已删除「${item.title}」`, position: 'top' })
    await load()
  } catch {
    // 统一错误提示由 http 层处理
  }
}

async function load(): Promise<void> {
  loading.value = true
  try {
    const data: Paginated<ExternalLink> = await fetchExternalLinks()
    links.value = data.results
  } catch {
    // 统一错误提示由 http 层处理
  } finally {
    loading.value = false
  }
}

function open(item: ExternalLink): void {
  if (item.open_in_new_tab) {
    window.open(item.url, '_blank', 'noopener,noreferrer')
  } else {
    window.location.href = item.url
  }
}

onMounted(load)
</script>

<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h6">外链入口</div>
        <div class="text-caption text-grey-6">
          通往其他平台的统一入口，点击即在新标签页打开
        </div>
      </div>
      <q-btn
        v-if="canManage"
        label="添加入口"
        icon="add"
        color="primary"
        unelevated
        @click="openCreate"
      />
    </div>

    <div v-if="loading" class="row justify-center q-pa-xl">
      <q-spinner-dots color="primary" size="34px" />
    </div>

    <template v-else-if="grouped.length">
      <div v-for="group in grouped" :key="group.category" class="q-mb-lg">
        <div class="group-title">
          <q-icon name="label" size="15px" />
          <span>{{ group.category }}</span>
          <q-badge outline color="grey-6" class="q-ml-xs">{{ group.items.length }}</q-badge>
        </div>

        <div class="row q-col-gutter-md">
          <div v-for="item in group.items" :key="item.id" class="col-12 col-sm-6 col-md-4">
            <q-card flat bordered class="link-card">
              <q-card-section>
                <div class="row items-start no-wrap">
                  <q-avatar
                    size="38px"
                    :color="item.is_active ? 'blue-1' : 'grey-3'"
                    :text-color="item.is_active ? 'primary' : 'grey-6'"
                  >
                    <q-icon :name="item.icon || 'link'" size="20px" />
                  </q-avatar>

                  <div class="col q-ml-md" style="min-width: 0">
                    <div class="row items-center no-wrap">
                      <div class="text-subtitle2 ellipsis">{{ item.title }}</div>
                      <q-badge
                        v-if="!item.is_active"
                        color="grey-5"
                        class="q-ml-sm"
                      >
                        已停用
                      </q-badge>
                    </div>
                    <div class="text-caption text-grey-6 q-mt-xs" style="word-break: break-all">
                      {{ item.description || item.url }}
                    </div>
                  </div>
                </div>
              </q-card-section>

              <q-separator />

              <q-card-actions align="right">
                <q-btn
                  flat
                  dense
                  no-caps
                  color="primary"
                  label="打开"
                  icon="open_in_new"
                  :disable="!item.is_active"
                  @click="open(item)"
                />
                <template v-if="canManage">
                  <q-btn flat dense round icon="edit" size="sm" @click="openEdit(item)">
                    <q-tooltip>编辑</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    round
                    icon="delete_outline"
                    size="sm"
                    color="negative"
                    @click="remove(item)"
                  >
                    <q-tooltip>删除</q-tooltip>
                  </q-btn>
                </template>
              </q-card-actions>
            </q-card>
          </div>
        </div>
      </div>
    </template>

    <q-card v-else flat bordered>
      <q-card-section class="text-center q-pa-xl">
        <q-icon name="link_off" size="42px" color="grey-5" />
        <div class="text-subtitle2 q-mt-md">还没有任何外链入口</div>
        <div class="text-caption text-grey-6 q-mt-xs">
          {{
            canManage
              ? '点击右上角「添加入口」，把常用的平台收纳进来'
              : '请联系管理员添加常用平台的入口'
          }}
        </div>
        <q-btn
          v-if="canManage"
          label="添加入口"
          icon="add"
          color="primary"
          unelevated
          class="q-mt-lg"
          @click="openCreate"
        />
      </q-card-section>
    </q-card>

    <!-- 新增 / 编辑 -->
    <q-dialog v-model="dialogVisible" persistent>
      <q-card style="width: 520px; max-width: 92vw">
        <q-card-section class="row items-center">
          <div class="text-subtitle1">
            {{ editingId === null ? '添加入口' : '编辑入口' }}
          </div>
          <q-space />
          <q-btn flat dense round icon="close" v-close-popup />
        </q-card-section>
        <q-separator />

        <q-card-section class="q-gutter-md">
          <q-input v-model="form.title" label="名称" outlined dense maxlength="64" />

          <q-input
            v-model="form.url"
            label="地址"
            outlined
            dense
            maxlength="512"
            hint="以 http://、https:// 或 / 开头"
          />

          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-6">
              <q-select
                v-model="form.icon"
                :options="ICON_OPTIONS"
                label="图标"
                outlined
                dense
                emit-value
                map-options
              >
                <template #option="scope">
                  <q-item v-bind="scope.itemProps">
                    <q-item-section avatar><q-icon :name="scope.opt" /></q-item-section>
                    <q-item-section>{{ scope.opt }}</q-item-section>
                  </q-item>
                </template>
                <template #prepend><q-icon :name="form.icon" /></template>
              </q-select>
            </div>
            <div class="col-12 col-sm-6">
              <q-input v-model="form.category" label="分组" outlined dense maxlength="32" />
            </div>
          </div>

          <q-input
            v-model="form.description"
            label="说明（可选）"
            outlined
            dense
            maxlength="255"
          />

          <div class="row q-col-gutter-md items-center">
            <div class="col-12 col-sm-6">
              <q-input v-model.number="form.order" type="number" label="排序" outlined dense />
            </div>
            <div class="col-12 col-sm-6">
              <q-toggle v-model="form.is_active" label="启用" />
              <q-toggle v-model="form.open_in_new_tab" label="新标签页打开" />
            </div>
          </div>

          <q-input
            v-model="form.required_perm"
            label="所需权限码"
            outlined
            dense
            hint="默认 portal.links.view，表示所有持该权限的成员可见"
          />
        </q-card-section>

        <q-separator />
        <q-card-actions align="right">
          <q-btn flat label="取消" v-close-popup />
          <q-btn
            label="保存"
            color="primary"
            unelevated
            :loading="saving"
            :disable="!form.title || !form.url"
            @click="save"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style scoped>
.group-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13.5px;
  font-weight: 600;
  color: #4a5875;
  margin-bottom: 10px;
}

.body--dark .group-title {
  color: #b6c2d9;
}

.link-card {
  height: 100%;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.link-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(16, 42, 80, 0.09);
}
</style>
