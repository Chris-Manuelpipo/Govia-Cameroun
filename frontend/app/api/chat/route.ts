import { NextRequest } from "next/server";
import { relayer } from "../../lib/backend";

export async function POST(req: NextRequest) {
  return relayer("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await req.text(),
  });
}
