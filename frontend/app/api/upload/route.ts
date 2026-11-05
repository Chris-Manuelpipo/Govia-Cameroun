import { NextRequest } from "next/server";
import { relayer } from "../../lib/backend";

export async function POST(req: NextRequest) {
  return relayer("/upload", { method: "POST", body: await req.formData() });
}
