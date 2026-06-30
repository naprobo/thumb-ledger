# Requirements Document

## Introduction

本系统是一款面向手机端的快速记账网页应用，支持用户注册、创建多个账本、灵活配置账本模式（是否记录花费对象），并以单手单指操作为核心交互设计，通过分屏向导式输入流程（Wizard Flow）快速完成每一笔记账。系统支持账本共享、智能排序偏好记忆、消费名称引导、多语言切换，以及用户建议收集与公开支持/反对反馈。

技术栈：FastAPI（后端）、Vue（前端）、PostgreSQL（数据库）。

---

## Glossary

- **User（用户）**: 已注册并登录系统的账户持有人；可选设置昵称（nickname），昵称存在时优先作为对其他用户显示的名称
- **Owner（账本持有人）**: 创建该账本的 User，拥有账本的最高权限
- **Ledger（账本）**: 用户创建的记账本，包含该账本的配置与所有交易记录
- **Transaction（交易）**: 账本中的一笔记录，可以是单张小票或单个商品
- **Entry_Mode（记录模式）**: 账本级别的配置，决定每次记账是"一张小票一笔"还是"每种商品一笔"
- **Subject（花费对象）**: 可选配置，标注该笔消费是为谁购买的（如"自己"、"孩子"、"爸爸"）
- **Subject_Step_Mode（花费对象步骤模式）**: 账本级别的配置，决定在 Wizard Flow 中花费对象步骤是"必须选择"还是"可跳过"；用户可在记账过程中关闭该步骤，也可在账本设置中随时重新开启
- **Necessity（消费必要性）**: 每笔消费的属性标签，分为"刚需"（essential，如食物、日用品）和"非刚需"（non-essential，如小饰品、改善性消费）
- **Necessity_Step_Mode（必要性步骤模式）**: 账本级别的配置，决定是否在 Wizard Flow 中显示"刚需/非刚需"选择步骤；默认关闭，开启后用户可在记账中途随时关闭
- **Category（分类 / 消费大类）**: 用于预算和统计的一级消费品类标签（如食物、服装、日用品、交通）。用户自定义 Category 时应表达相对稳定的大类，而不是一次性明细费用。
- **Item（消费名称 / 明细）**: 属于某个 Category 下的具体消费名称（如"牛奶"、"T恤"、"油费"、"车检"）。
- **Location（消费地点）**: 每笔交易可选的消费场所文本（如"公司附近超市"）；历史输入按用户偏好排序供下次选择。
- **Location_Step_Mode（消费地点步骤模式）**: 账本级别的配置，决定消费地点步骤是必须输入、可跳过还是关闭。
- **Suggestion（建议）**: 用户提交给系统运营者的功能需求、问题反馈或改进意见，可选择公开以寻求其他用户支持或反对
- **Suggestion_Vote（建议投票）**: 用户对公开 Suggestion 表达支持或反对的记录，每个用户对同一建议最多保留一个当前立场
- **Notification（通知）**: 系统向用户提示待处理共享申请、审批结果等事件的机制；MVP 采用顶部通知铃铛、通知列表与可选邮件通知
- **Wizard_Flow（向导流程）**: 分屏步进式输入界面，每屏只呈现一个输入步骤
- **Preference_Engine（偏好引擎）**: 记录用户选择频次并对标签排序的后端模块
- **Share_Request（共享申请）**: 某 User 申请加入某 Ledger 的待审核请求
- **Share_Role（共享角色）**: 共享用户在账本中的权限级别，分为"只读"（read-only）和"可写"（read-write）
- **Admin（系统管理员）**: 拥有最高权限的特殊用户角色，可管理所有用户账号和系统配置
- **Password_Reset_Token（密码重置令牌）**: 发送至用户邮箱的一次性短期令牌，用于密码找回流程
- **Migration（数据库迁移）**: 使用版本化脚本对数据库 schema 进行可追溯的增量变更
- **Currency_Code（货币代码）**: 遵循 ISO 4217 标准的三字母货币代码（如 JPY、CNY、USD）；MVP 采用一账本一货币，不在单笔交易中混用货币
- **Recurring_Transaction（定期交易）**: 按预设周期自动生成的交易记录（如每月房租、水电费）
- **Audit_Log（审计日志）**: 记录关键操作（登录、共享变更、Admin 操作）的时间戳与来源 IP 的系统日志
- **Budget（预算）**: 账本级别的可选功能，设定月度或年度总支出上限及各 Category 的细分金额
- **Budget_Service（预算服务）**: 负责预算配置的创建、查询与超支提醒的后端模块
- **Budget_Wizard（预算向导）**: 账本创建后引导用户逐屏设置预算的分屏流程，每步均可跳过
- **Admin_Service（管理员服务）**: 负责系统管理员操作的后端模块，包括用户管理和系统配置
- **Ledger_Service（账本服务）**: 负责账本创建、配置、共享与管理的后端模块
- **Transaction_Service（交易服务）**: 负责交易记录的创建、查询与统计的后端模块
- **I18n_Service（国际化服务）**: 负责多语言文案加载与切换的前端模块
- **API**: 后端提供的 RESTful HTTP 接口
- **Token（令牌）**: 用于身份验证的 JWT access token

---

## Requirements

### Requirement 1：用户注册与登录

**User Story:** As a new user, I want to register and log in, so that I can securely access my personal ledgers.

#### Acceptance Criteria

1. THE Auth_Service SHALL provide a registration endpoint that accepts a unique email address and a password of at least 8 characters.
1a. THE Auth_Service SHALL allow registration to include an optional nickname; WHEN nickname is omitted, THE System SHALL use the User's email as the fallback display name.
2. WHEN a registration request is received with a duplicate email, THE Auth_Service SHALL return an error indicating the email is already in use.
3. WHEN a valid login request is received, THE Auth_Service SHALL return a JWT Token with an expiry of 7 days.
4. IF a login request contains an incorrect email or password, THEN THE Auth_Service SHALL return an authentication failure error without revealing which field is incorrect.
5. WHILE a Token is valid, THE API SHALL accept the Token in the Authorization header to authenticate requests.
6. WHEN a Token has expired, THE API SHALL return a 401 Unauthorized response.

---

### Requirement 1c：个人信息与密码修改

**User Story:** As a logged-in user, I want to manage my display name and password, so that shared ledgers can identify me clearly and my account remains secure.

#### Acceptance Criteria

1. THE System SHALL provide a Profile page accessible from the authenticated top-right menu.
2. THE Profile page SHALL display the User's email and nickname.
3. THE Profile page SHALL allow the User to create, update, or clear their nickname.
4. WHEN a User is displayed in shared-ledger member lists, share requests, notifications, or admin views, THE System SHALL prefer nickname and fall back to email.
5. THE Profile page SHALL allow the User to change their password by entering the current password and a new password of at least 8 characters.
6. WHEN a password is changed successfully, THE Auth_Service SHALL invalidate existing JWT Tokens for that User and require re-login.
7. THE Profile page SHOULD expose account deletion as a clearly separated danger-zone action, because it is already part of account lifecycle management and should not be hidden in general settings.

---

### Requirement 1b：密码找回

**User Story:** As a user who has forgotten my password, I want to receive a reset link by email, so that I can regain access to my account.

#### Acceptance Criteria

1. THE Auth_Service SHALL provide a password reset request endpoint that accepts a registered email address.
2. WHEN a password reset request is received for a registered email, THE Auth_Service SHALL generate a Password_Reset_Token with an expiry of 30 minutes and send it to that email address.
3. WHEN a password reset request is received for an email that does not exist in the system, THE Auth_Service SHALL return the same success response as a valid request to prevent email enumeration.
4. THE Auth_Service SHALL provide a password reset confirmation endpoint that accepts a Password_Reset_Token and a new password of at least 8 characters.
5. WHEN a valid Password_Reset_Token and a new password are received, THE Auth_Service SHALL update the User's password and invalidate the Password_Reset_Token immediately.
6. WHEN an expired or already-used Password_Reset_Token is received, THE Auth_Service SHALL return an error indicating the token is invalid or expired.
7. WHEN a password is successfully reset, THE Auth_Service SHALL invalidate all existing JWT Tokens for that User, requiring re-login.

---

### Requirement 2：账本创建与配置

**User Story:** As a logged-in user, I want to create a ledger and configure its options, so that I can tailor the bookkeeping experience to my needs.

#### Acceptance Criteria

1. THE Ledger_Service SHALL allow a User to create a new Ledger with a name of 1 to 50 characters.
2. WHEN a Ledger is created, THE Ledger_Service SHALL require the User to select an Entry_Mode: either "receipt"（一张小票一笔）or "item"（每种商品一笔）.
3. WHEN a Ledger is created, THE Ledger_Service SHALL require the User to choose whether Subject tracking is enabled for that Ledger.
4. WHEN Subject tracking is enabled during Ledger creation, THE Ledger_Service SHALL require the User to set the Subject_Step_Mode: either "required"（每笔必须选择花费对象）or "optional"（花费对象步骤可跳过）.
5. WHEN a Ledger is created, THE Ledger_Service SHALL allow the User to enable Necessity tracking; Necessity_Step_Mode SHALL default to "disabled" if not explicitly enabled.
6. WHEN Budget is enabled during Ledger creation, THE Budget_Wizard SHALL launch immediately after the Ledger configuration step.
7. THE Ledger_Service SHALL allow a User to own up to 10 Ledgers simultaneously.
8. IF a User attempts to create more than 10 Ledgers, THEN THE Ledger_Service SHALL return an error indicating the maximum Ledger limit has been reached.
9. THE Ledger_Service SHALL allow a User to update the Ledger name, Subject_Step_Mode, and Necessity_Step_Mode after creation from the Ledger settings screen.
10. WHEN Entry_Mode is "receipt", THE Ledger_Service SHALL allow the User to enable an optional spending-detail step; the same setting SHALL remain editable from Ledger settings.
11. THE Ledger_Service SHALL allow the User to configure Location_Step_Mode as "required", "optional", or "disabled" during creation and from Ledger settings; the default SHALL be "optional".
12. THE Ledger creation Wizard SHALL configure receipt details, Subject, Necessity, and Location on separate screens using large tag-style choices; receipt details SHALL offer "偶尔会记录详细" and "不会记录详细", while the other tracking screens SHALL offer "必须记录", "可以跳过", and "不会记录".
13. THE Ledger creation Wizard SHALL keep timezone as an internal system default and SHALL NOT ask the User to enter it on the default-currency screen.

---

### Requirement 3：花费对象（Subject）管理

**User Story:** As a user, I want to select from pre-set family member subjects and add my own, so that I can track who each expense is for without manual typing.

#### Acceptance Criteria

1. WHERE Subject tracking is enabled, THE Ledger_Service SHALL pre-populate the Subject list with the following default tags: 自己、爸爸、妈妈、孩子、爷爷、奶奶、老公、老婆、兄弟、姐妹.
2. WHERE Subject tracking is enabled, THE Ledger_Service SHALL allow the User to append custom Subject names beyond the pre-set list, up to a combined total of 20 Subjects per Ledger.
3. THE Ledger_Service SHALL allow the User to delete custom Subject names but SHALL NOT allow deletion of pre-set Subject names.
4. WHEN a User selects a Subject, THE Preference_Engine SHALL increment the selection count for that Subject in that Ledger.
5. THE Preference_Engine SHALL return the Subject list sorted by selection count descending, with ties broken by the original list order.

---

### Requirement 4：分类与消费名称引导

**User Story:** As a user, I want to choose a spending name from suggestions, and when needed first narrow it by category, so that I can minimize manual typing.

#### Acceptance Criteria

1. THE Transaction_Service SHALL require the User to select a Category for each Transaction from the following pre-defined list: 食品饮料、外食餐饮、日用品、服饰鞋包、居住、水电燃气、通信网络、交通出行、汽车用车、医疗健康、保险、教育学习、育儿子女、宠物、娱乐休闲、旅行住宿、数码家电、订阅会员、社交礼金、美容护理、税费手续费、其他.
2. WHEN Entry_Mode is "item", after a Category is selected, THE Transaction_Service SHALL present a list of suggested Item names belonging to that Category for the User to tap-select.
3. THE Transaction_Service SHALL pre-populate each Category with at least 5 common Item name suggestions.
4. THE Product SHALL NOT expose custom Category creation in the normal user flow; Category is a fixed system-provided budget/statistics dimension.
5. THE UI SHOULD explain that Category is a budget/statistics-level spending group and Item is the place for detailed costs such as 油费 or 车检.
6. WHEN the User selects a suggested Item name, THE Transaction_Service SHALL record that name without requiring manual text input.
7. WHERE the User requires an Item name not in the suggestion list, THE Transaction_Service SHALL present a tappable "+ 自定义" chip in the Item name tag list and reveal a text input field only after that chip is selected; the confirmation OK control SHALL appear immediately beside the text input.
8. WHEN Entry_Mode is "receipt", THE Wizard_Flow SHALL require Category selection after Amount; WHEN receipt spending details are enabled, it SHALL show an Item name step that can be skipped, otherwise it SHALL save the generated TransactionItem with an empty Item name.
9. WHEN a User selects a Category or Item name, THE Preference_Engine SHALL increment the selection count for that tag within its Ledger and Category scope.
10. THE Preference_Engine SHALL return Category and Item name suggestions sorted by selection count descending, with ties broken by the original default order.
11. WHEN Location_Step_Mode is not disabled, THE Wizard_Flow SHALL present a Location step after Item name (when present) and before Necessity.
12. THE Location step SHALL display previously used locations ordered by the current User's selection count and provide a "+ 追加" action that reveals a text input only after being tapped.
13. WHEN Location_Step_Mode is "optional", the Location step SHALL provide a one-tap skip action; WHEN it is "required", skipping or saving an empty location SHALL not be allowed.
14. THE Transaction_Service SHALL persist Location as a transaction-level text snapshot and expose it in transaction detail/update APIs and CSV export.
15. WHEN editing a Transaction, THE UI SHALL allow both Item name and Location to be selected from their preference lists or entered as free-form text; selecting a localized system Item SHALL preserve its original translation key.
16. THE Wizard_Flow SHALL provide edit and hide modes for custom Category, Item, Location, and Subject tags; system-provided tags SHALL NOT be editable or removable.
17. THE System SHALL assign stable IDs to custom tags. Renaming a custom tag SHALL update historical transaction display, while hiding it SHALL only remove it from selection lists and SHALL NOT delete historical references.
18. WHEN a User adds a tag whose same-name custom record is hidden in the same scope, THE System SHALL restore that record and reuse its original ID.

---

### Requirement 5：分屏向导式输入（Wizard Flow）

**User Story:** As a mobile user, I want to enter each transaction field on its own screen step, so that each screen is simple and easy to operate with one finger.

#### Acceptance Criteria

1. WHEN a User starts recording a new Transaction, THE Wizard_Flow SHALL present the steps in the following order for item mode: 金额（Amount） → 分类（Category） → 消费名称（Item name） → 消费地点（Location，未关闭时） → 必要性（Necessity，仅在 Necessity_Step_Mode 启用时出现） → 花费对象（Subject，仅在 Subject tracking 启用时出现）.
1a. WHEN Entry_Mode is "receipt", THE Wizard_Flow SHALL present the steps in the following order: 金额（Amount） → 分类（Category） → 消费名称（仅在账本启用消费细节时出现且可跳过） → 消费地点（Location，未关闭时） → 必要性（Necessity，仅在 Necessity_Step_Mode 启用时出现） → 花费对象（Subject，仅在 Subject tracking 启用时出现）.
2. WHEN the User completes input on one Wizard_Flow step, THE Wizard_Flow SHALL automatically advance to the next step without requiring a manual "next" tap.
3. THE Wizard_Flow SHALL display only the content for the current step on screen, with no other steps visible simultaneously.
4. THE Wizard_Flow SHALL display a consistent title bar on every step; the Amount step title SHALL be "输入金额".
4a. THE Wizard_Flow SHALL allow the User to navigate back with a single tap from the title bar: on the Amount step this returns to the Ledger home, and on later steps this returns to the previous step.
4b. WHEN THE Wizard_Flow advances to a new step or to the completion prompt, THE visible scroll position SHALL reset to the top of the Wizard screen.
5. WHEN the User reaches the final step and confirms, THE Wizard_Flow SHALL save the Transaction and display a completion prompt.
6. WHEN Entry_Mode is "item", THE Wizard_Flow SHALL create one Transaction containing one Category-guided Item name. Multi-item entry is deferred beyond MVP to avoid losing partially entered multi-step state during network interruption or accidental navigation.
7. WHEN Subject_Step_Mode is "optional", THE Wizard_Flow SHALL display a "以后不再问" (skip and don't ask again) option on the Subject selection step, operable with a single tap.
8. WHEN the User taps "以后不再问" on the Subject step, THE Ledger_Service SHALL set Subject_Step_Mode to "disabled" for that Ledger, and THE Wizard_Flow SHALL omit the Subject step in all subsequent Transactions for that Ledger.
9. WHEN Subject_Step_Mode is "disabled", THE Ledger_Service SHALL allow the Owner to re-enable it from the Ledger settings screen, which SHALL restore Subject_Step_Mode to "optional".
10. WHEN Necessity_Step_Mode is "enabled", THE Wizard_Flow SHALL present a two-option selection on the Necessity step: "刚需"（essential）and "非刚需"（non-essential）; no option SHALL be preselected and no automatic timeout SHALL save or advance the Transaction.
11. WHEN Necessity_Step_Mode is "enabled", THE Wizard_Flow SHALL display a "关闭此步骤" option on the Necessity step as the same large tappable tile style as the normal choices.
12. WHEN the User taps "关闭此步骤" on the Necessity step, THE Ledger_Service SHALL set Necessity_Step_Mode to "disabled", and THE Wizard_Flow SHALL omit the Necessity step in all subsequent Transactions, recording all future Transactions as "刚需" by default.
13. WHEN Necessity_Step_Mode is "disabled", THE Transaction_Service SHALL record the Necessity of each Transaction as "essential" without prompting the User.
14. THE Wizard_Flow SHALL NOT display Ledger home actions, settings controls, budget panels, or transaction lists while a Transaction is being recorded.
15. THE Wizard_Flow SHALL NOT display an intermediate save button; the Transaction SHALL be saved only after the final configured step is explicitly completed.

---

### Requirement 6：完成提示与继续操作

**User Story:** As a user, I want to be prompted after saving a transaction to either record another or return home, so that I can maintain my recording flow without extra navigation.

#### Acceptance Criteria

1. WHEN a Transaction is saved successfully, THE Transaction_Service SHALL display a completion prompt within 300ms offering two options: "再记一笔" and "完成，回到主页".
2. WHEN the User selects "再记一笔", THE Wizard_Flow SHALL immediately reset and start a new Transaction entry from the Amount step.
3. WHEN the User selects "完成，回到主页", THE System SHALL navigate the User to the Ledger transaction list.
4. THE completion prompt SHALL be operable with a single tap on either option.
5. THE completion prompt SHALL use the same title-bar position as other Wizard_Flow steps, display "记录成功" as the title, and SHALL NOT provide a back action.

---

### Requirement 7：快速新建一笔交易（核心流程）

**User Story:** As a user, I want to quickly record a new transaction with a single thumb, so that bookkeeping does not interrupt my daily flow.

#### Acceptance Criteria

1. WHEN a User opens a Ledger, THE Transaction_Service SHALL present a compact plus icon action beside the Ledger name to start recording a new Transaction; Ledger settings SHALL be represented by a gear icon beside it with enough spacing to reduce accidental taps.
2. WHEN Entry_Mode is "receipt", THE Transaction_Service SHALL require a total amount and Category, with no mandatory Item name breakdown; if spending details are enabled, the User MAY select, enter, or skip the Item name.
3. WHEN Entry_Mode is "item", THE Transaction_Service SHALL allow the User to record one item with an amount and a Category-guided name per Wizard run.
4. THE Transaction_Service SHALL allow the User to record the transaction date, defaulting to the current date.
5. THE Transaction_Service SHALL record a Currency_Code (ISO 4217) for each Transaction, defaulting to the Ledger's configured currency.
6. WHEN a Transaction is saved successfully, THE Transaction_Service SHALL persist the record and return a success response within 500ms.

---

### Requirement 8：自制金额数字键盘

**User Story:** As a mobile user, I want the app to show its own dial-pad-style amount keypad immediately when recording a transaction, so that I can enter amounts without relying on the system input method.

#### Acceptance Criteria

1. WHEN the User starts recording a new Transaction, THE Wizard_Flow SHALL immediately show a custom in-app numeric keypad on the Amount step without focusing a native amount input.
2. THE Amount step SHALL display the current amount above the keypad in a calculator-like display using the Ledger's default Currency_Code.
3. THE custom keypad SHALL include digit keys 0-9, a clear/delete control, and an OK key that confirms the amount and advances the Wizard_Flow.
4. THE Amount step SHALL NOT depend on the browser or OS numeric keyboard for primary amount entry.
5. THE System SHALL render other currency and budget amount input fields with `inputmode="numeric"` where native text entry is still used.
6. WHEN a non-numeric value is submitted in an Amount field, THE Transaction_Service SHALL return a validation error.

---

### Requirement 9：账本共享

**User Story:** As a ledger owner, I want to share my ledger with other users, so that we can record expenses together.

#### Acceptance Criteria

1. THE Ledger_Service SHALL allow a User to submit a Share_Request to join a Ledger by providing the Ledger's share code or link.
2. WHEN a Share_Request is received, THE Ledger_Service SHALL notify the Owner of that Ledger by making the request visible in the owner's pending requests list and, when email delivery is configured, by sending an email notification.
3. WHEN the Owner approves a Share_Request, THE Ledger_Service SHALL grant the requesting User access to that Ledger according to the Share_Role selected by the Owner: "read-write" allows creating Transactions; "read-only" allows viewing Transactions and summaries only.
4. WHEN the Owner rejects a Share_Request, THE Ledger_Service SHALL remove or mark the Share_Request as rejected and notify the requesting User through the application state and, when email delivery is configured, by sending an email notification.
5. THE Ledger_Service SHALL allow the Owner to remove a previously approved shared User from the Ledger at any time.
6. WHEN a shared User is removed, THE Ledger_Service SHALL immediately revoke that User's access to the Ledger.
7. THE Ledger_Service SHALL allow a Ledger to have at most 10 shared Users in addition to the Owner.
8. THE Ledger_Service SHALL display the list of current shared Users to the Owner.
9. WHEN the Owner taps the share-code control in Ledger settings, THE frontend SHALL display the share code with a copy icon button beside the code field.
10. WHEN the copy icon is tapped, THE frontend SHALL copy the share code to the clipboard and show a top-floating toast below the app bar.
11. THE authenticated top-right menu SHALL provide an entry for joining a shared Ledger by entering a share code or opening a share link.
12. THE Ledger settings screen SHALL display pending Share_Requests to the Owner, using requester display name (nickname fallback email), requested role, status, and approve/reject actions.
13. THE Owner SHALL be able to choose or modify the approved member's Share_Role as read-only or read-write.
14. THE shared member list SHALL display each member by nickname when available, otherwise by email.
15. WHEN the Owner taps a member name, THE System SHALL open a member detail screen where the Owner can change the member's role or stop/remove sharing for that member.
16. WHEN sharing is stopped or a member is removed, THE System SHALL create an in-app Notification for the affected member.

---

### Requirement 10：智能排序（偏好记忆）

**User Story:** As a frequent user, I want the tags I select most often to appear at the top of each list, so that I can tap my usual choices with minimal scrolling.

#### Acceptance Criteria

1. THE Preference_Engine SHALL record each User's selection count per tag (Subject, Category, Item name) per Ledger independently.
2. WHEN a tag list is rendered, THE Preference_Engine SHALL sort tags by the User's selection count for that Ledger in descending order.
3. WHEN two tags have equal selection counts, THE Preference_Engine SHALL preserve the original default order as a tiebreaker.
4. WHEN a User has no prior selections in a Ledger, THE Preference_Engine SHALL present tags in the default order.
5. THE Preference_Engine SHALL update selection counts within 1000ms of a Transaction being saved.

---

### Requirement 11：单指操作原则

**User Story:** As a mobile user, I want to complete the entire transaction recording process with a single finger, so that I can record expenses one-handed.

#### Acceptance Criteria

1. THE System SHALL render all interactive controls (buttons, selectors, inputs) with a minimum tap target size of 44×44 CSS pixels.
2. THE System SHALL present Category, Subject, and Item name selection as tappable chip lists or grids requiring no more than 1 tap per selection.
3. THE System SHALL present Entry_Mode and Subject tracking configuration as toggle switches operable with a single tap.
4. WHEN a Transaction amount is required, THE System SHALL display its custom in-app numeric keypad immediately, without requiring the User to open or switch the OS keyboard.
5. THE System SHALL complete the entire Wizard_Flow Transaction entry, from opening the first step to displaying the completion prompt, using no more than one tap per step.
6. THE System SHALL support viewport widths from 320px to 480px without horizontal scrolling.
7. WHERE the User needs to create a custom Subject, Category, or Item name, THE System SHALL provide a text input field as the sole exception to the single-finger tap-only flow.
8. THE System SHALL render Wizard_Flow choice screens such as Item name, Necessity, Subject, and completion actions as large tile-style controls suitable for one-finger operation.

---

### Requirement 12：交易列表与查看

**User Story:** As a user, I want to view my transaction history, so that I can review my spending.

#### Acceptance Criteria

1. WHEN a User opens a Ledger, THE Transaction_Service SHALL display a list of Transactions ordered by transaction date descending.
2. THE Transaction_Service SHALL display each Transaction with at minimum: date, amount, category, and note (if present).
3. WHERE Subject tracking is enabled, THE Transaction_Service SHALL display the Subject for each Transaction in the list.
4. THE Transaction_Service SHALL allow the Ledger transaction list to be filtered by date range so the frontend can display one month at a time.
5. THE Transaction_Service SHALL display the total expenditure sum for the current month being viewed.
6. THE frontend SHALL label the Ledger history section as "消费记录", show a compact one-row-per-record list where possible, and navigate months using previous-month and next-month controls rather than page-number pagination.

---

### Requirement 13：交易统计汇总

**User Story:** As a user, I want to see spending summaries by category and subject, so that I can understand where my money goes.

#### Acceptance Criteria

1. WHEN a User requests a summary for a Ledger, THE Transaction_Service SHALL return the total expenditure grouped by Category for a user-selected time range.
2. WHERE Subject tracking is enabled, WHEN a User requests a summary, THE Transaction_Service SHALL return the total expenditure grouped by Subject for the selected time range.
3. WHERE Necessity_Step_Mode has been enabled for a Ledger, WHEN a User requests a summary, THE Transaction_Service SHALL return the total expenditure split by Necessity（刚需 vs 非刚需）for the selected time range.
4. THE Transaction_Service SHALL support time range selection of: 本周、本月、本年、自定义区间.
5. WHEN a custom time range is selected with a start date later than the end date, THE Transaction_Service SHALL return an error indicating an invalid date range.

---

### Requirement 14：多语言支持

**User Story:** As a user, I want to switch the app language between Chinese, English, and Japanese, so that I can use the app in my preferred language.

#### Acceptance Criteria

1. THE I18n_Service SHALL support the following three languages: 简体中文（zh-CN）、English（en）、日本語（ja）.
2. THE System SHALL allow the User to switch the display language from the authenticated top-right menu with a single tap selection; language is a user preference, not a Ledger property.
3. WHEN the User selects a language, THE I18n_Service SHALL apply the new language to all UI text within 300ms without requiring a page reload.
4. THE I18n_Service SHALL persist the User's language preference and apply it automatically on subsequent sessions.
5. WHEN no language preference is stored, THE I18n_Service SHALL default to the language reported by the browser's `navigator.language`, falling back to 简体中文 if the reported language is not among the supported three.
6. THE I18n_Service SHALL translate all static UI text, labels, error messages, and pre-set Subject and Category names into each supported language.

---

### Requirement 15：数据持久化与一致性

**User Story:** As a user, I want my data to be reliably stored, so that I never lose a transaction record.

#### Acceptance Criteria

1. THE API SHALL persist all Transaction records to the PostgreSQL database before returning a success response to the client.
2. WHEN a database write fails, THE API SHALL return a 500 error to the client and SHALL NOT return a success response.
3. THE API SHALL enforce that each Transaction belongs to exactly one Ledger and one User, and SHALL reject requests that violate this constraint.
4. WHEN a Ledger is deleted by its Owner, THE Ledger_Service SHALL delete all Transactions and Share_Requests associated with that Ledger.

---

### Requirement 16：系统管理员

**User Story:** As a system administrator, I want to manage all user accounts and system settings, so that I can maintain the platform's health and security.

#### Acceptance Criteria

1. THE Admin_Service SHALL support a designated Admin user role that is distinct from ordinary Users and is assigned directly in the database or via a secure CLI command.
2. WHEN an Admin authenticates, THE Auth_Service SHALL issue a Token that includes the Admin role claim.
3. THE Admin_Service SHALL provide an endpoint to list all registered Users, including their email, registration date, and account status.
4. THE Admin_Service SHALL allow an Admin to disable or re-enable any User account.
5. WHEN a User account is disabled, THE API SHALL reject all requests authenticated with that User's Token and return a 403 Forbidden response.
6. THE Admin_Service SHALL allow an Admin to delete any User account along with all associated Ledgers and Transactions.
7. THE Admin_Service SHALL allow an Admin to view aggregate system statistics: total User count, total Ledger count, and total Transaction count.
8. ALL Admin_Service endpoints SHALL reject requests from non-Admin Tokens with a 403 Forbidden response.

---

### Requirement 17：前端安全与注入防护

**User Story:** As a system operator, I want the application to be protected against common injection attacks, so that user data and system integrity are preserved.

#### Acceptance Criteria

1. THE API SHALL use parameterized queries or an ORM that generates parameterized queries for all database interactions, preventing SQL injection.
2. THE API SHALL validate and sanitize all user-supplied string inputs on the server side before processing or persisting them.
3. THE System SHALL set the Content-Security-Policy HTTP header on all HTML responses to restrict executable script sources.
4. IF the System uses cookies for authentication or session state in the future, THEN those cookies SHALL set `HttpOnly`, `Secure`, and `SameSite` attributes; the current Bearer JWT design SHALL NOT store the access token in cookies.
5. THE API SHALL enforce a maximum length on all string input fields and return a 422 Unprocessable Entity error when the limit is exceeded.
6. THE System SHALL escape all user-generated content before rendering it in the Vue frontend to prevent XSS injection.
7. THE API SHALL reject requests with unexpected Content-Type headers for endpoints that accept a request body.

---

### Requirement 18：数据库迁移管理

**User Story:** As a developer, I want all database schema changes to be managed through versioned migration scripts, so that the database can be upgraded safely across environments.

#### Acceptance Criteria

1. THE System SHALL use Alembic as the database migration tool, integrated with the FastAPI application's SQLAlchemy models.
2. EVERY database schema change SHALL be expressed as a numbered, ordered Alembic migration script with both an `upgrade` and a `downgrade` function.
3. WHEN the application starts, THE System SHALL automatically apply all pending Alembic migrations before accepting traffic.
4. THE System SHALL maintain an `alembic_version` table in the PostgreSQL database to track the currently applied migration revision.
5. IT SHALL be possible to roll back the database to any previous migration revision by running the corresponding `downgrade` command without modifying application code.
6. Migration scripts SHALL NOT contain hard-coded environment-specific values; all such values SHALL be sourced from environment variables.

---

### Requirement 19：预算功能

**User Story:** As a user, I want to set monthly and annual budgets for my ledger and optionally break them down by category, so that I can track whether my spending stays within plan.

#### Acceptance Criteria

1. WHEN Budget is enabled for a Ledger, THE Budget_Service SHALL store a monthly total budget amount and an optional annual total budget amount for that Ledger.
2. WHEN Budget is enabled, THE Budget_Wizard SHALL guide the User through the following steps in order, each on a separate screen:
   - Step 1: 输入月度总预算金额（必填，数字键盘输入）
   - Step 2: 是否设置年度总预算（可跳过，跳过则年度预算 = 月度预算 × 12）
   - Step 3: 是否细分各 Category 预算金额（可跳过）
   - Step 4（仅在 Step 3 未跳过时出现）: 逐个 Category 输入细分预算金额（每个 Category 单独一屏，均可跳过）
3. AT ANY STEP of the Budget_Wizard, THE System SHALL display a "跳过，使用默认设置" option operable with a single tap; WHEN tapped, THE Budget_Wizard SHALL complete immediately using system defaults for all remaining steps.
4. THE default Category budget allocation SHALL distribute the monthly total budget equally across all active Categories when the User skips Step 3.
5. WHEN the User completes or exits the Budget_Wizard, THE Budget_Service SHALL persist the configured budget with whatever values were provided, using defaults for any skipped steps.
6. WHEN the sum of Category budget amounts entered in Step 4 exceeds the monthly total budget, THE Budget_Wizard SHALL display a warning but SHALL still allow the User to save.
7. THE Budget_Service SHALL allow the User to update any budget amount from the Ledger settings screen at any time.
8. THE Budget_Service SHALL allow the User to disable the Budget feature from the Ledger settings screen at any time.

---

### Requirement 20：预算进度提示

**User Story:** As a user with a budget set, I want to see how much of my budget I have used, so that I can adjust my spending before exceeding the limit.

#### Acceptance Criteria

1. WHEN a User views a Ledger with Budget enabled, THE Budget_Service SHALL display the current month's total spending against the monthly total budget as a progress indicator.
2. WHERE Category budgets are configured, THE Budget_Service SHALL display per-Category spending progress alongside the transaction list summary.
3. WHEN a Transaction is saved that causes total monthly spending to reach or exceed 80% of the monthly total budget, THE Budget_Service SHALL display a soft warning notification to the User.
4. WHEN a Transaction is saved that causes total monthly spending to exceed 100% of the monthly total budget, THE Budget_Service SHALL display an over-budget alert to the User.
5. THE Budget_Service SHALL calculate budget progress in real time based on Transactions within the current calendar month.
6. WHEN the Budget feature is disabled for a Ledger, THE Budget_Service SHALL hide all budget progress indicators for that Ledger.

---

### Requirement 21：账本货币支持（ISO 4217）

**User Story:** As a user, I want each ledger to have a clear currency, so that records and totals remain simple and predictable.

#### Acceptance Criteria

1. WHEN a Ledger is created, THE Ledger_Service SHALL require the User to select a default Currency_Code from the ISO 4217 standard (e.g. JPY, CNY, USD).
2. WHEN a new Transaction is started, THE Wizard_Flow SHALL use the Ledger's default Currency_Code.
3. THE Product SHALL NOT expose per-Transaction currency override in MVP; mixed-currency ledgers are deferred for future discussion.
4. THE Transaction_Service SHALL store amounts as integers in the smallest unit of the selected currency (e.g. yen for JPY, fen for CNY, cents for USD) to avoid floating-point precision errors.
5. WHEN displaying amounts, THE System SHALL format them according to the selected Currency_Code and the User's locale.
6. THE Transaction_Service SHALL keep currency_code on Transactions for data integrity and future compatibility, but normal MVP UI SHALL present one currency per Ledger.

---

### Requirement 22：小票图片附件（Future / Deferred）

**User Story:** As a user, I want to attach a photo of my receipt to a transaction, so that I have a visual record for verification.

#### Acceptance Criteria

1. Image attachment is not part of the first usable release scope.
2. Existing backend image APIs MAY remain as dormant infrastructure, but the MVP frontend SHALL NOT be required to expose image upload, thumbnail preview, or image deletion UI.
3. WHEN image attachment is resumed in a future release, THE System SHOULD allow up to 3 JPEG/PNG images per Transaction, each no larger than 5 MB, stored outside PostgreSQL binary columns.
4. Future image attachment SHALL be optional and SHALL NOT block fast Transaction saving.

---

### Requirement 23：定期交易

**User Story:** As a user, I want to set up recurring transactions for fixed expenses, so that I do not need to manually record them every period.

#### Acceptance Criteria

1. THE Transaction_Service SHALL allow a User to mark any Transaction as a template for a Recurring_Transaction with a recurrence interval of: 每天、每周、每月、每年.
2. WHEN a Recurring_Transaction is configured, THE Transaction_Service SHALL automatically generate a new Transaction based on the template on each scheduled date.
3. THE Transaction_Service SHALL generate recurring Transactions at midnight (00:00) in the Ledger's configured timezone on the scheduled date.
4. THE Transaction_Service SHALL allow the User to edit or delete a Recurring_Transaction template at any time; changes SHALL NOT affect already-generated past Transactions.
5. WHEN a Recurring_Transaction is deleted, THE Transaction_Service SHALL stop generating future Transactions but SHALL retain all previously generated Transaction records.
6. THE System SHALL display a list of active Recurring_Transaction templates within the Ledger settings screen.

---

### Requirement 24：数据导出

**User Story:** As a user, I want to export my transaction data to a file, so that I can review it in a spreadsheet or share it with others.

#### Acceptance Criteria

1. THE Transaction_Service SHALL provide a CSV export endpoint for a Ledger, returning all Transactions within a user-specified date range.
2. THE exported CSV SHALL include the following columns: date, amount, currency_code, category, item_name, location, subject (if enabled), necessity (if enabled), note, recorded_by.
3. THE Transaction_Service SHALL complete the CSV export request within 5 seconds for up to 10,000 Transactions.
4. THE System SHALL set the Content-Disposition header to trigger a file download in the browser.
5. THE System SHALL keep the export layer extensible so that OFX export can be added later without changing the Transaction data model; MVP support is CSV only.

---

### Requirement 25：安全加固

**User Story:** As a system operator, I want the application to follow security hardening best practices, so that user data and accounts are protected against common attacks.

#### Acceptance Criteria

1. THE Auth_Service SHALL enforce rate limiting on the login endpoint: no more than 10 failed attempts per IP per 15-minute window, after which requests SHALL receive a 429 Too Many Requests response.
2. THE Auth_Service SHALL enforce rate limiting on the password reset request endpoint: no more than 5 requests per email address per hour.
3. THE Auth_Service SHALL enforce rate limiting on the registration endpoint: no more than 10 registrations per IP per hour.
4. THE System SHALL serve all public traffic exclusively over HTTPS; in Cloudflare Tunnel deployments, HTTPS enforcement and HTTP-to-HTTPS 301 redirects SHALL be configured at Cloudflare, while internal Docker network traffic may use HTTP.
5. THE System SHALL set the Strict-Transport-Security (HSTS) header with a minimum max-age of 31536000 seconds on all responses.
6. THE Auth_Service SHALL hash all passwords using bcrypt with a minimum work factor of 12 before storing them in the database.
7. THE System SHALL write an Audit_Log entry for each of the following events: successful login, failed login, password reset, Ledger share approval/rejection, shared User removal, and any Admin_Service action.
8. EACH Audit_Log entry SHALL record: event type, User ID, timestamp (UTC), and source IP address.
9. THE Audit_Log SHALL be stored in a append-only database table; no application-level endpoint SHALL allow deletion or modification of Audit_Log entries.

---

### Requirement 26：账号注销

**User Story:** As a user, I want to permanently delete my account and all associated data, so that I can exercise my right to be forgotten.

#### Acceptance Criteria

1. THE Auth_Service SHALL provide an account deletion endpoint accessible to authenticated Users.
2. WHEN an account deletion request is received, THE System SHALL require the User to confirm by entering their current password before proceeding.
3. WHEN account deletion is confirmed, THE System SHALL permanently delete: the User record, all Ledgers owned by the User, all Transactions in those Ledgers, all Share_Requests sent or received by the User, all Preference_Engine data, and all Audit_Log entries attributable to that User.
4. WHEN account deletion is confirmed, THE System SHALL immediately invalidate all JWT Tokens for that User.
5. THE System SHALL complete the full deletion within 30 seconds and return a 200 success response upon completion.
6. WHEN a User who is a shared member (not Owner) of a Ledger deletes their account, THE Ledger_Service SHALL remove that User from the shared list but SHALL NOT delete the Ledger or its Transactions.

---

### Requirement 27：用户建议与公开支持

**User Story:** As a user, I want to submit suggestions and optionally make them public, so that I can tell the service operator what I need and seek support from other users.

#### Acceptance Criteria

1. THE Suggestion_Service SHALL allow an authenticated User to create a Suggestion with a title of 1 to 100 characters and a body of 1 to 2000 characters.
2. WHEN creating a Suggestion, THE User SHALL be able to choose whether the Suggestion is public.
3. THE System SHALL provide a "提出建议" entry from the authenticated top-right menu that opens a dedicated Suggestion page.
4. THE Suggestion page SHALL allow the User to submit a new Suggestion and view a list of their own Suggestions.
5. THE Suggestion page SHALL provide a separate tab for public Suggestions submitted by other Users.
6. WHEN a Suggestion is public, other authenticated Users SHALL be able to express support or opposition.
7. THE Suggestion_Service SHALL allow each User to have at most one current vote per public Suggestion; changing from support to opposition or opposition to support SHALL update the existing vote instead of creating a duplicate.
8. THE Suggestion_Service SHALL NOT allow the Suggestion author to vote on their own Suggestion.
9. THE Suggestion_Service SHALL expose support and opposition counts for each public Suggestion.
10. THE Admin_Service SHALL provide an admin-only Suggestions view listing all Suggestions, including private Suggestions, author email, public status, support count, opposition count, created time, and current status.
11. THE Admin_Service SHALL allow an Admin to mark a Suggestion as new, reviewing, planned, completed, or declined.
12. ALL Suggestion_Service and Admin Suggestion endpoints SHALL enforce authentication, authorization, string length validation, and XSS-safe rendering.

---

### Requirement 28：通知中心

**User Story:** As a user, I want to see important sharing events from a notification bell, so that I do not miss requests or approval results.

#### Acceptance Criteria

1. THE authenticated app header SHALL display a notification bell icon immediately to the left of the top-right menu.
2. WHEN unread Notifications exist, THE bell SHALL show a red dot indicator.
3. WHEN the User taps the bell, THE System SHALL open a Notification view or drawer listing recent Notifications.
4. Notification items SHALL include at minimum: type, human-readable message, related Ledger display name where applicable, created time, and read/unread state.
5. THE System SHALL create a Notification when another User requests to join one of the Owner's Ledgers.
6. THE System SHALL create a Notification when a Share_Request is approved or rejected.
7. THE System SHALL create a Notification when a shared member's role is changed or their sharing access is removed.
8. THE User SHALL be able to mark Notifications as read; after all are read, the bell red dot SHALL disappear.
9. Notification text SHALL use i18n messages and display Users by nickname when available, otherwise email.
