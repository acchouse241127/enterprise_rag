import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getKnowledgeBases } from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MessageSquare, Database, FileText, BarChart3 } from "lucide-react";

export default function Home() {
  const [kbCount, setKbCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getKnowledgeBases()
      .then((res) => setKbCount(res.data?.length || 0))
      .catch((e) => console.debug("Failed to load KB count:", e))
      .finally(() => setLoading(false));
  }, []);

  const quickActions = [
    {
      title: "智能问答",
      description: "向知识库提问，获取 AI 生成的答案",
      icon: MessageSquare,
      href: "/qa",
      color: "text-blue-600",
    },
    {
      title: "知识库管理",
      description: "创建和管理知识库，上传文档",
      icon: Database,
      href: "/kb",
      color: "text-green-600",
    },
    {
      title: "对话记录",
      description: "查看历史对话，分享给他人",
      icon: FileText,
      href: "/conversations",
      color: "text-purple-600",
    },
    {
      title: "数据看板",
      description: "查看系统使用统计和检索质量",
      icon: BarChart3,
      href: "/dashboard",
      color: "text-orange-600",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">欢迎使用 Enterprise RAG</h1>
        <p className="text-muted-foreground mt-2">
          企业级知识库问答系统，助您高效获取知识
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              知识库数量
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {loading ? "..." : kbCount}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              V2.0 新特性
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              混合检索 + 置信度评估 + 智能拒答
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              快速开始
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Link to="/qa">
              <Button>开始提问</Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* 快捷入口 */}
      <div>
        <h2 className="text-xl font-semibold mb-4">快捷入口</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Link key={action.href} to={action.href}>
              <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="pt-6">
                  <action.icon className={`h-8 w-8 mb-3 ${action.color}`} />
                  <h3 className="font-semibold">{action.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {action.description}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
