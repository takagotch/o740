
void OnStart()
{
  string useSymbol = CloseSymbol;
  if(CloseSymbol == "") use Symbol = _Symbol;

  if(PositionType(useSymbol) != WRONG_VALUE)
  {
    bool closed = Trade.Close(useSymbol);
    if(closed == true)
    {
      Comment("Position closed on "+useSymbol");
    }
  }

  if(Pending.TotalPending(useSymbol) > 0)
  {
    ulong tickets[];
    Pending.GetTickets(useSymbol,tickets);
    int numTickets = ArraySize(tickets);

    for(int i = 0; i < numTickets; i++)
    {
      Trade.Delete(tickets[i]);
    }

    if(Pending.TotalPending(useSymbol) == 0)
    {
      Comment("All pending orders closed on "+useSymbol");
    }
  }
}


