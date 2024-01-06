import java
import semmle.code.java.dataflow.DataFlow
import semmle.code.java.frameworks.android.Intent

// Does data param from onActivityResult method flow into an argument in setResult methodcall
from MethodCall onActivityResult, MethodCall setResult, Expr data
where onActivityResult.getMethod().hasName("onActivityResult") and 
    setResult.getMethod().hasName("setResult") and 
    onActivityResult.getArgument(2) = data and 
    DataFlow::localFlow(DataFlow::exprNode(data), DataFlow::exprNode(setResult.getAnArgument()))
select data, setResult, "data param from onActivityResult flows into setResult method call"

// from MethodCall setResult, Parameter p
// where setResult.getMethod().hasName("setResult") and
// DataFlow::localFlow(DataFlow::parameterNode(p) , DataFlow::exprNode(setResult.getArgument(1))) //find flow from a parameter source to an expression sink in zero or more local steps
// select setResult, p





