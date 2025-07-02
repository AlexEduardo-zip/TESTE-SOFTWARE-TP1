from fastapi import HTTPException
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label, Input, Static
from textual.screen import Screen
from textual.containers import Container


from tsbanking.services import (
    consultar_saldo, depositar, sacar, transferir,
    consultar_extrato, aplicar_investimento, resgatar_investimento, saque_caixa
)
from tsbanking.models import TipoInvestimento, TipoCaixa


class BancoApp(App):
    CSS_PATH = "style.tcss"
    BINDINGS = [("q", "quit", "Sair")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(Label("Bem-vindo ao Banco Digital!", id="titulo"))
        yield Button("Acessar Conta", id="login", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login":
            self.push_screen(LoginScreen())


class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Login", classes="titulo")
        yield Input(placeholder="Nome da Conta", id="conta")
        yield Button("Entrar", id="entrar")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "entrar":
            conta = self.query_one("#conta", Input).value
            if conta in ["principal", "destino"]:  # Validação simples
                self.app.push_screen(MenuScreen(conta))
            else:
                self.notify("Conta inválida!", severity="error")


class MenuScreen(Screen):
    def __init__(self, conta: str):
        super().__init__()
        self.conta = conta

    def compose(self) -> ComposeResult:
        yield Label(f"Menu Principal ({self.conta})", classes="titulo")
        yield Button("Saldo", id="saldo")
        yield Button("Depósito", id="deposito")
        yield Button("Saque", id="saque")
        yield Button("Transferência", id="transferencia")
        yield Button("Extrato", id="extrato")
        yield Button("Investimentos", id="investimentos")
        yield Button("Sair", id="sair")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "saldo":
            self.app.push_screen(SaldoScreen(self.conta))
        elif event.button.id == "deposito":
            self.app.push_screen(OperacaoScreen(self.conta, "deposito"))
        elif event.button.id == "saque":
            self.app.push_screen(OperacaoScreen(self.conta, "saque"))
        elif event.button.id == "transferencia":
            self.app.push_screen(TransferenciaScreen(self.conta))
        elif event.button.id == "extrato":
            self.app.push_screen(ExtratoScreen(self.conta))
        elif event.button.id == "investimentos":
            self.app.push_screen(InvestimentosScreen(self.conta))
        elif event.button.id == "sair":
            self.app.pop_screen()


class SaldoScreen(Screen):
    def __init__(self, conta: str):
        super().__init__()
        self.conta = conta

    def compose(self) -> ComposeResult:
        saldo = consultar_saldo(self.conta)
        yield Label(f"Saldo: R$ {saldo:.2f}", classes="resultado")
        yield Button("Voltar", id="voltar")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class OperacaoScreen(Screen):
    def __init__(self, conta: str, operacao: str):
        super().__init__()
        self.conta = conta
        self.operacao = operacao

    def compose(self) -> ComposeResult:
        yield Label(f"{self.operacao.capitalize()}", classes="titulo")
        yield Input(placeholder="Valor (R$)", id="valor", restrict=r"^[0-9]*\.?[0-9]*$")
        yield Button("Confirmar", id="confirmar")
        yield Button("Cancelar", id="cancelar")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirmar":
            if (self.query_one("#valor", Input).value.strip() == ""):
                self.notify("Por favor, informe um valor válido!",
                            severity="error")
                return
            if (float(self.query_one("#valor", Input).value) <= 0):
                self.notify("Valor deve ser maior que zero!", severity="error")
                return

            valor = float(self.query_one("#valor", Input).value)
            if self.operacao == "deposito":
                try:
                    depositar(valor, self.conta)
                    self.notify(
                        f"Depósito de R$ {valor:.2f} realizado!", severity="success")
                    self.app.pop_screen()
                except HTTPException as e:
                    self.notify(f"Erro: {e.detail}", severity="error")
                except Exception as e:
                    self.notify(f"Erro inesperado: {str(e)}", severity="error")
            elif self.operacao == "saque":
                try:
                    sacar(valor, self.conta)
                    self.notify(
                        f"Saque de R$ {valor:.2f} realizado!", severity="success")
                    self.app.pop_screen()
                except HTTPException as e:
                    self.notify(f"Erro: {e.detail}", severity="error")
                except Exception as e:
                    self.notify(f"Erro inesperado: {str(e)}", severity="error")

        elif event.button.id == "cancelar":
            self.app.pop_screen()


class TransferenciaScreen(Screen):
    def __init__(self, conta: str):
        super().__init__()
        self.conta = conta

    def compose(self) -> ComposeResult:
        yield Label("Transferência", classes="titulo")
        yield Input(placeholder="Conta Destino", id="destino")
        yield Input(placeholder="Valor (R$)", id="valor", restrict=r"^[0-9]*\.?[0-9]*$")
        yield Button("Confirmar", id="confirmar")
        yield Button("Cancelar", id="cancelar")

    def on_button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "confirmar":
            if (self.query_one("#valor", Input).value.strip() == ""):
                self.notify("Por favor, informe um valor válido!",
                            severity="error")
                return
            if (float(self.query_one("#valor", Input).value) <= 0):
                self.notify("Valor deve ser maior que zero!", severity="error")
                return

            try:
                destino = self.query_one("#destino", Input).value
                valor = float(self.query_one("#valor", Input).value)
                transferir(valor, destino, self.conta)
                self.notify(
                    f"Transferência de R$ {valor:.2f} para {destino}!", severity="success")
                self.app.pop_screen()
            except HTTPException as e:
                self.notify(f"Erro: {e.detail}", severity="error")
            except Exception as e:
                self.notify(f"Erro inesperado: {str(e)}", severity="error")

        elif event.button.id == "cancelar":
            self.app.pop_screen()


class ExtratoScreen(Screen):
    def __init__(self, conta: str):
        super().__init__()
        self.conta = conta

    def compose(self) -> ComposeResult:
        extrato = consultar_extrato(self.conta)
        yield Label("Extrato", classes="titulo")
        yield Static("\n".join([f"{op['op']}: R$ {op['valor']:.2f}" for op in extrato]), classes="extrato")
        yield Button("Voltar", id="voltar")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class InvestimentosScreen(Screen):
    def __init__(self, conta: str):
        super().__init__()
        self.conta = conta

    def compose(self) -> ComposeResult:
        yield Label("Investimentos", classes="titulo")
        yield Button("Aplicar", id="aplicar")
        yield Button("Resgatar", id="resgatar")
        yield Button("Voltar", id="voltar")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "aplicar":
            self.app.push_screen(AplicarInvestimentoScreen(self.conta))
        elif event.button.id == "resgatar":
            self.app.push_screen(ResgatarInvestimentoScreen(self.conta))
        elif event.button.id == "voltar":
            self.app.pop_screen()


class AplicarInvestimentoScreen(Screen):
    def __init__(self, conta: str):
        super().__init__()
        self.conta = conta

    def compose(self) -> ComposeResult:
        yield Label("Aplicar em Investimento", classes="titulo")
        yield Input(placeholder="Valor (R$)", id="valor", restrict=r"^[0-9]*\.?[0-9]*$")
        yield Button("CDB (1.5%)", id="CDB")
        yield Button("Poupança (0.5%)", id="POUPANCA")
        yield Button("Tesouro Direto (1%)", id="TESOURO_DIRETO")
        yield Button("Voltar", id="voltar")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ["CDB", "POUPANCA", "TESOURO_DIRETO"]:
            if (self.query_one("#valor", Input).value.strip() == ""):
                self.notify("Por favor, informe um valor válido!",
                            severity="error")
                return
            if (float(self.query_one("#valor", Input).value) <= 0):
                self.notify("Valor deve ser maior que zero!", severity="error")
                return

            try:
                valor = float(self.query_one("#valor", Input).value)
                aplicar_investimento(
                    valor, event.button.id.upper(), self.conta)
                self.notify(
                    f"Aplicado R$ {valor:.2f} em {event.button.id}!", severity="success")
                self.app.pop_screen()
            except HTTPException as e:
                self.notify(f"Erro: {e.detail}", severity="error")
            except Exception as e:
                self.notify(f"Erro inesperado: {str(e)}", severity="error")

        elif event.button.id == "voltar":
            self.app.pop_screen()


class ResgatarInvestimentoScreen(Screen):
    def __init__(self, conta: str):
        super().__init__()
        self.conta = conta

    def compose(self) -> ComposeResult:
        yield Label("Resgatar Investimento", classes="titulo")
        yield Button("CDB", id="CDB")
        yield Button("Poupança", id="POUPANCA")
        yield Button("Tesouro Direto", id="TESOURO_DIRETO")
        yield Button("Voltar", id="voltar")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ["CDB", "POUPANCA", "TESOURO_DIRETO"]:
            try:
                resgatar_investimento(event.button.id.upper(), self.conta)
                self.notify(
                    f"Resgatado investimento em {event.button.id}!", severity="success")
                self.app.pop_screen()
            except HTTPException as e:
                self.notify(f"Erro: {e.detail}", severity="error")
            except Exception as e:
                self.notify(f"Erro inesperado: {str(e)}", severity="error")

        elif event.button.id == "voltar":
            self.app.pop_screen()


if __name__ == "__main__":
    app = BancoApp()
    app.run()
