import { NextRequest } from "next/server";
import { relayer } from "../../lib/backend";

export async function GET(req: NextRequest) {
  const langue = req.nextUrl.searchParams.get("langue") === "EN" ? "EN" : "FR";
  return relayer(`/consentement?langue=${langue}`);
}
