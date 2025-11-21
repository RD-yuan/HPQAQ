# 项目协作规范

为了保证团队的开发效率、避免代码冲突和 main 分支被破坏，所有成员必须遵循以下协作规范。

---

# 1. 分支模型说明

本项目采用以下分支模型：

```
main            最稳定版本，随时可用于演示/验收
dev             日常开发集成分支
feature/xxx     每个功能一个分支
hotfix/xxx      紧急修复(热补丁)
```

### ✔ main（受保护）

* 永远可运行、可展示
* 不允许直接 push
* 只能通过 Pull Request 合并

### ✔ dev（开发集成）

* 日常开发代码的汇总
* 所有 feature 分支最终都要合并到 dev

### ✔ feature/xxx（功能开发）

* 每个人开发自己的功能时从 dev 开分支
* 命名示例：

  * `feature/frontend-login-page`
  * `feature/api-user-auth`
  * `feature/spider-lianjia`

### ✔ hotfix/xxx（紧急修复）

* 必须从 main 拉取
* 修复后先合到 main，再同步回 dev

---

# 2. 开发流程

## Step 1：更新 dev 分支

```bash
git checkout dev
git pull origin dev
```

## Step 2：从 dev 拉出自己的 feature 分支

```bash
git checkout -b feature/你的功能名
```

例子：

```bash
git checkout -b feature/spider-lianjia
```

## Step 3：在 feature 分支上开发并提交

```bash
git add .
git commit -m "实现链家爬虫基础框架"
git push origin feature/spider-lianjia
```

## Step 4：提交 Pull Request（PR）

在 GitHub 上发 PR：

> base: **dev** ← compare: **feature/xxx**

内容需包含：

* 本次修改目的
* 完成内容
* 未完成内容（如果有）

## Step 5：至少一人 Review 后合并到 dev

大家互相审核。

---

# 3. main 分支发布流程（由管理员负责）

当 dev 足够稳定且可运行：

1. 管理员发起 PR：
   `dev -> main`
2. 由管理员审核并合并
3. 打一个 tag（版本号）：

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

这样 main 永远是最稳定版本。

---

# 🧯 4. 紧急修复（hotfix）

如果 main 已经被用来演示，但发现 bug，需要立刻修复：

```bash
git checkout main
git pull origin main
git checkout -b hotfix/fix-login-bug
```

修完后：

1. 提 PR：`hotfix -> main`
2. 合并后，再发 PR：`main -> dev`
   让 dev 同步修复。

---

# 🔒 5. 分支保护要求（管理员已设置）

* main 不允许直接 push
* main 必须 PR + approve 才能合并
* main 不允许删除
* dev 可允许协作者 push（也可以保护）
* feature 分支自由

---

# 📝 6. Commit 信息格式

参考以下格式：

```
feat: 新增房价趋势图表组件
fix: 修复接口跨域问题
refactor: 优化爬虫结构
docs: 更新 README 和接口说明
style: 调整格式，不影响代码逻辑
```

---

# 🎉 7. 开发注意事项

* 不要在 main 上改任何东西。
* 不要把自己的 feature 分支互相合并。
* 所有修改都通过 PR 合并。
* 合并前在本地先跑一遍项目确保能启动。