import os
from pathlib import Path

p = Path("ops/src/pages/Tasks.tsx")
content = p.read_text(encoding="utf-8")

# 1. Add useAuth import
if "import { useAuth }" not in content:
    content = content.replace(
        "import { api, KanbanTask, KanbanBoardView } from '../lib/api'",
        "import { api, KanbanTask, KanbanBoardView } from '../lib/api'\nimport { useAuth } from '../lib/auth'"
    )

# 2. Update staffList and Tasks component initialization
old_init = """const staffList = [
  { code: 'all', name: 'Tất cả nhân viên' },
  { code: 'NV', name: 'Nguyễn Văn (NV)', bg: 'bg-slate-800 text-white' },
  { code: 'LT', name: 'Lê Tuấn (LT)', bg: 'bg-blue-800 text-white' },
  { code: 'TH', name: 'Trần Hùng (TH)', bg: 'bg-slate-800 text-white' },
  { code: 'TM', name: 'Trần Minh (TM)', bg: 'bg-blue-800 text-white' },
]

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>(initialTasksData)"""

new_init = """export const Tasks: React.FC = () => {
  const { user } = useAuth()
  const [tasks, setTasks] = useState<TaskItem[]>(initialTasksData)
  const [staffList, setStaffList] = useState<Array<{ code: string; name: string; username?: string; bg?: string }>>([
    { code: 'all', name: 'Tất cả nhân viên' },
    { code: 'my_tasks', name: '⭐ Việc của tôi' },
    { code: 'LT', name: 'Lê Tuấn (Quản lý CSKH)', username: 'ql_tuan', bg: 'bg-blue-800 text-white' },
    { code: 'NV', name: 'Nguyễn Văn An (Kỹ thuật)', username: 'nv_an', bg: 'bg-slate-800 text-white' },
    { code: 'LT', name: 'Lê Thảo (Tư vấn bán hàng)', username: 'nv_thao', bg: 'bg-blue-800 text-white' },
    { code: 'TM', name: 'Trần Minh (Chăm sóc sau bán)', username: 'nv_minh', bg: 'bg-blue-800 text-white' },
    { code: 'TH', name: 'Trần Hùng (Xử lý khiếu nại)', username: 'nv_hung', bg: 'bg-slate-800 text-white' },
  ])"""

content = content.replace(old_init.replace("\n", "\r\n"), new_init.replace("\n", "\r\n"))
content = content.replace(old_init, new_init)

# 3. Add dynamic load tasks and dynamic load staff
old_load = """  useEffect(() => {
    loadBackendTasks()
  }, [])"""

new_load = """  // Load real staff from API
  useEffect(() => {
    api.getUsers().then((res) => {
      if (res?.users && res.users.length > 0) {
        const dynamicStaff = res.users.map((u: any) => ({
          code: u.code || (u.name ? u.name.split(' ').map((p: string) => p[0]).join('').slice(0, 2).toUpperCase() : 'NV'),
          name: `${u.name || u.username} (${u.role === 'manager' ? 'Quản lý' : 'Nhân viên'})`,
          username: u.username,
          bg: u.role === 'manager' ? 'bg-blue-800 text-white' : 'bg-slate-800 text-white',
        }))
        setStaffList([
          { code: 'all', name: 'Tất cả nhân viên' },
          { code: 'my_tasks', name: '⭐ Việc của tôi' },
          ...dynamicStaff,
        ])
      }
    }).catch(() => {})
  }, [])

  // Load real tasks from backend
  const loadOpsTasks = async () => {
    try {
      const res = await (api as any).getOpsTasks()
      if (res?.ok && res.tasks && res.tasks.length > 0) {
        setTasks(res.tasks)
      }
    } catch (_) {}
  }

  useEffect(() => {
    loadOpsTasks()
    loadBackendTasks()
  }, [])"""

content = content.replace(old_load.replace("\n", "\r\n"), new_load.replace("\n", "\r\n"))
content = content.replace(old_load, new_load)

# 4. Make handleMoveTask save to backend
old_move = """  const handleMoveTask = (taskId: string, targetCol: 'todo' | 'in_progress' | 'waiting' | 'done') => {
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, columnId: targetCol } : t))
    )
  }"""

new_move = """  const handleMoveTask = async (taskId: string, targetCol: 'todo' | 'in_progress' | 'waiting' | 'done') => {
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, columnId: targetCol } : t))
    )
    try {
      await (api as any).moveOpsTask(taskId, targetCol)
    } catch (e) {
      console.error('Lỗi cập nhật cột task:', e)
    }
  }"""

content = content.replace(old_move.replace("\n", "\r\n"), new_move.replace("\n", "\r\n"))
content = content.replace(old_move, new_move)

# 5. Make handleCreateTask save to backend
old_create = """    setTasks((prev) => [newTask, ...prev])
    setIsAddModalOpen(false)
    setNewTitle('')
    setNewCustomer('')
  }"""

new_create = """    setTasks((prev) => [newTask, ...prev])
    setIsAddModalOpen(false)
    setNewTitle('')
    setNewCustomer('')
    try {
      await (api as any).createOpsTask(newTask)
    } catch (e) {
      console.error('Lỗi tạo task backend:', e)
    }
  }"""

content = content.replace(old_create.replace("\n", "\r\n"), new_create.replace("\n", "\r\n"))
content = content.replace(old_create, new_create)

# 6. Update counts in columnsConfig
old_cols = """  const columnsConfig = [
    {
      id: 'todo' as const,
      title: 'Cần làm',
      count: 12,
      headerColor: 'text-slate-900',
      badgeBg: 'bg-slate-100 text-slate-700',
      columnBg: 'bg-slate-50/70 border-slate-200/80',
    },
    {
      id: 'in_progress' as const,
      title: 'Đang xử lý',
      count: 8,
      headerColor: 'text-blue-600',
      badgeBg: 'bg-blue-50 text-blue-700',
      columnBg: 'bg-blue-50/20 border-blue-100',
    },
    {
      id: 'waiting' as const,
      title: 'Chờ phản hồi',
      count: 5,
      headerColor: 'text-amber-600',
      badgeBg: 'bg-amber-50 text-amber-700',
      columnBg: 'bg-amber-50/20 border-amber-100',
    },
    {
      id: 'done' as const,
      title: 'Hoàn tất',
      count: 28,
      headerColor: 'text-emerald-600',
      badgeBg: 'bg-emerald-50 text-emerald-700',
      columnBg: 'bg-emerald-50/20 border-emerald-100',
    },
  ]"""

new_cols = """  const columnsConfig = [
    {
      id: 'todo' as const,
      title: 'Cần làm',
      count: tasks.filter((t) => t.columnId === 'todo').length,
      headerColor: 'text-slate-900',
      badgeBg: 'bg-slate-100 text-slate-700',
      columnBg: 'bg-slate-50/70 border-slate-200/80',
    },
    {
      id: 'in_progress' as const,
      title: 'Đang xử lý',
      count: tasks.filter((t) => t.columnId === 'in_progress').length,
      headerColor: 'text-blue-600',
      badgeBg: 'bg-blue-50 text-blue-700',
      columnBg: 'bg-blue-50/20 border-blue-100',
    },
    {
      id: 'waiting' as const,
      title: 'Chờ phản hồi',
      count: tasks.filter((t) => t.columnId === 'waiting').length,
      headerColor: 'text-amber-600',
      badgeBg: 'bg-amber-50 text-amber-700',
      columnBg: 'bg-amber-50/20 border-amber-100',
    },
    {
      id: 'done' as const,
      title: 'Hoàn tất',
      count: tasks.filter((t) => t.columnId === 'done').length,
      headerColor: 'text-emerald-600',
      badgeBg: 'bg-emerald-50 text-emerald-700',
      columnBg: 'bg-emerald-50/20 border-emerald-100',
    },
  ]"""

content = content.replace(old_cols.replace("\n", "\r\n"), new_cols.replace("\n", "\r\n"))
content = content.replace(old_cols, new_cols)

# 7. Update filteredTasks for my_tasks
old_filter = """  const filteredTasks = tasks.filter((t) => {
    if (rescueFilter === 'rescue' && !t.rescueStage) return false
    if (selectedStaff !== 'all' && t.assignee.code !== selectedStaff) return false"""

new_filter = """  const filteredTasks = tasks.filter((t) => {
    if (rescueFilter === 'rescue' && !t.rescueStage) return false
    if (selectedStaff === 'my_tasks') {
      const myUname = (user?.username || '').toLowerCase()
      const myName = (user?.name || '').toLowerCase()
      const aUname = (t.assignee as any)?.username?.toLowerCase() || ''
      const aName = (t.assignee?.name || '').toLowerCase()
      const aCode = (t.assignee?.code || '').toLowerCase()
      const matches = (myUname && aUname === myUname) ||
        (myName && aName.includes(myName)) ||
        (myUname && myUname.includes(aCode))
      if (!matches) return false
    } else if (selectedStaff !== 'all') {
      const a = t.assignee as any
      if (a?.code !== selectedStaff && a?.username !== selectedStaff) return false
    }"""

content = content.replace(old_filter.replace("\n", "\r\n"), new_filter.replace("\n", "\r\n"))
content = content.replace(old_filter, new_filter)

p.write_text(content, encoding="utf-8")
print("SUCCESS: Tasks.tsx updated")
