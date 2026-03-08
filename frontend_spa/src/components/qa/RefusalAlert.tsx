import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

interface RefusalAlertProps {
  reason: string;
  message: string;
}

export function RefusalAlert({ reason, message }: RefusalAlertProps) {
  const getReasonTitle = (reason: string) => {
    switch (reason) {
      case "empty_retrieval":
        return "知识库中未找到相关内容";
      case "low_relevance":
        return "检索内容与问题相关性过低";
      case "low_faithfulness":
        return "无法生成可靠的回答";
      default:
        return "无法提供可靠回答";
    }
  };

  return (
    <Alert variant="destructive" className="my-4">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{getReasonTitle(reason)}</AlertTitle>
      <AlertDescription className="whitespace-pre-wrap">{message}</AlertDescription>
    </Alert>
  );
}
