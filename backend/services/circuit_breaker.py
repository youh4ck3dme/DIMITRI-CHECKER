"""
Circuit Breaker pattern pre externé API
Chráni pred kaskádovými zlyhaniami pri výpadkoch externých služieb
"""

from enum import Enum
from typing import Callable, Optional, Any
from datetime import datetime


class CircuitState(Enum):
    """Stavy Circuit Breaker"""
    CLOSED = "closed"  # Normálny stav - požiadavky prechádzajú
    OPEN = "open"  # Zlyhanie - požiadavky sú blokované
    HALF_OPEN = "half_open"  # Testovací stav - obmedzené požiadavky


class CircuitBreaker:
    """
    Circuit Breaker implementácia pre ochranu externých API.
    
    Použitie:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=requests.RequestException
        )
        
        try:
            result = breaker.call(api_function, arg1, arg2)
        except CircuitBreakerOpenError:
            # Circuit je otvorený - použiť fallback
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "default"
    ):
        """
        Args:
            failure_threshold: Počet zlyhaní pred otvorením circuitu
            recovery_timeout: Sekundy pred pokusom o obnovenie
            expected_exception: Typ exception, ktorý sa považuje za zlyhanie
            name: Názov circuit breakeru (pre logging)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        self.half_open_success_threshold = 2  # Počet úspešných volaní pre uzavretie
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Volá funkciu cez Circuit Breaker.
        
        Args:
            func: Funkcia na volanie
            *args, **kwargs: Argumenty pre funkciu
            
        Returns:
            Výsledok funkcie
            
        Raises:
            CircuitBreakerOpenError: Ak je circuit otvorený
        """
        # Skontrolovať stav
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Last failure: {self.last_failure_time}"
                )
        
        # Skúsiť volanie
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Skontroluje, či by sa mal pokúsiť o reset"""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Spracuje úspešné volanie"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_success_threshold:
                # Úspešne obnovené
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                print(f"✅ Circuit breaker '{self.name}' CLOSED (recovered)")
        else:
            # V CLOSED stave - resetovať počítadlo zlyhaní
            self.failure_count = 0
    
    def _on_failure(self):
        """Spracuje zlyhané volanie"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Zlyhanie v HALF_OPEN - vrátiť sa do OPEN
            self.state = CircuitState.OPEN
            self.success_count = 0
            print(f"⚠️ Circuit breaker '{self.name}' OPEN (failed in half-open)")
        elif self.failure_count >= self.failure_threshold:
            # Dosiahnutý threshold - otvoriť circuit
            self.state = CircuitState.OPEN
            print(f"⚠️ Circuit breaker '{self.name}' OPEN (threshold reached: {self.failure_count})")
    
    def get_state(self) -> dict:
        """Vráti aktuálny stav circuit breakeru"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }
    
    def reset(self):
        """Manuálne resetovať circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        print(f"🔄 Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Exception vyvolaná keď je circuit breaker otvorený"""
    pass


# Globálne circuit breakery pre rôzne služby
_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """
    Získa alebo vytvorí circuit breaker pre danú službu.
    
    Args:
        name: Názov služby (napr. 'ares', 'rpo', 'krs')
        **kwargs: Parametre pre CircuitBreaker
        
    Returns:
        CircuitBreaker inštancia
    """
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name, **kwargs)
    return _breakers[name]


def get_all_breakers() -> dict[str, dict]:
    """Vráti stav všetkých circuit breakerov"""
    return {name: breaker.get_state() for name, breaker in _breakers.items()}


def reset_breaker(name: str):
    """Resetuje circuit breaker"""
    if name in _breakers:
        _breakers[name].reset()


def reset_all_breakers():
    """Resetuje všetky circuit breakery"""
    for breaker in _breakers.values():
        breaker.reset()

