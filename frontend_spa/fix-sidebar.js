const fs = require("fs");
let c = fs.readFileSync("src/components/layout/AppSidebar.tsx", "utf8");

// fix variable name
c = c.replace("const navigate = useLocation();", "const location = useLocation();");

// remove onClick block
c = c.replace(
  /onClick=\{[^}]*\n[^}]*\n[^}]*\n[^}]*\n[^}]*\}\s*/g,
  ""
);

// replace className function with location-based string (Link does not support render prop)
c = c.replace(
  /className=\{\(\{ isActive \}\) =>\s*cn\(\s*"flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",\s*isActive\s*\?\s*"bg-primary\/10 text-primary font-medium"\s*:\s*"text-muted-foreground hover:bg-accent hover:text-accent-foreground",\s*collapsed && "justify-center px-2"\s*\)\}/s,
  'className={cn("flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors", location.pathname === item.to ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground", collapsed && "justify-center px-2")}'
);

// restore Chinese labels (fix encoding corruption)
const labels = {
  "鏅鸿兘闂瓟": "智能问答",
  "鐭ヨ瘑搴撶鐞?": "知识库管理",
  "瀵硅瘽璁板綍": "对话记录",
  "鏁版嵁鐪嬫澘": "数据看板",
  "鏂囦欢澶瑰悓姝?": "文件夹同步",
  "寮傛浠诲姟": "异步任务",
};
for (const [bad, good] of Object.entries(labels)) {
  c = c.replace(bad, good);
}

fs.writeFileSync("src/components/layout/AppSidebar.tsx", c, "utf8");
console.log("AppSidebar.tsx updated");
