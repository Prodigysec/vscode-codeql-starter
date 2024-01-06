// 1: Write a query that finds all hard-coded strings used to create a java.net.URL, using local data flow

import java
import semmle.code.java.dataflow.DataFlow
import semmle.code.java.StringFormat
import semmle.code.java.dataflow.FlowSources

// from Constructor url, Call call, StringLiteral src 
// where url.getDeclaringType().hasQualifiedName("java.net", "URL") and 
//     call.getCallee() = url and 
//     DataFlow::localFlow(DataFlow::exprNode(src), DataFlow::exprNode(call.getArgument(0)))
// select src


// 2. Find the file name passed to new FileReader
// from Constructor fileReader, Call call
// where fileReader.getDeclaringType().hasQualifiedName("java.io.","FileReader") and 
//     call.getCallee() = fileReader
// select call.getArgument(0)

// 2.1 use local data flow to find all expressions that flow into the argument:
// from Constructor fileReader, Call call, Expr src
// where fileReader.getDeclaringType().hasQualifiedName("java.io.","FileReader")  and 
//     call.getCallee() = fileReader and
//     DataFlow::localFlow(DataFlow::exprNode(src), DataFlow::exprNode(call.getArgument(0)))
// select src

// 2.3 make source more specific, eg: an access to a public parameter. This query finds where a public parameter is passed to new FileReader(..):
// from Constructor fileReader, Call call, Parameter src
// where fileReader.getDeclaringType().hasQualifiedName("java.io.","FileReader")  and 
//     call.getCallee() = fileReader and
//     DataFlow::localFlow(DataFlow::parameterNode(src), DataFlow::exprNode(call.getArgument(0)))
// select src

// 3 get calls to formatting functions where format string is not hard-coded.
// from StringFormatMethod format, MethodCall call, Expr formatString
// where call.getMethod() = format and
//     call.getArgument(format.getFormatStringIndex()) = formatString and 
//     not exists(DataFlow::Node source, DataFlow::Node sink |
//         source.asExpr() instanceof StringLiteral and
//         sink.asExpr() = formatString and
//         DataFlow::localFlow(source, sink)
//     )
// select call, "Argument to String format method isn't hard-coded."




// GLOBAL DATA FLOW

// 2: Write a query that finds all hard-coded strings used to create a java.net.URL, using global data flow.
// module MyFlowConfiguration implements DataFlow::ConfigSig {
//   predicate isSource(DataFlow::Node source) {
//     source.asExpr() instanceof StringLiteral
//   }

//   predicate isSink(DataFlow::Node sink) {
//     exists(Call call |
//         call.getCallee().(Constructor).getDeclaringType().hasQualifiedName("java.net", "URL") and
//         sink.asExpr() = call.getArgument(0)
//     )
//   }
// }
// module MyFlow = DataFlow::Global<MyFlowConfiguration>;


// from DataFlow::Node src, DataFlow::Node sink
// where MyFlow::flow(src, sink)
// select src, "This string constructs a URL $@.", sink, "here"


// 3: Write a class that represents flow sources from java.lang.System.getenv(..).
class GetecSource extends MethodCall{
    GetenvSource(){
        exists(Method m | m = this.getMethod() |
        m.hasName("getenv") and
        m.getDeclaringType() instanceof TypeSystem
      )
    }
}


// 4: Using the answers from 2 and 3, write a query which finds all global data flows from getenv to java.net.URL.
