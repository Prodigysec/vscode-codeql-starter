import java
import semmle.code.java.dataflow.DataFlow

// 1: Write a query that finds all hard-coded strings used to create a java.net.URL, using local data flow
// from Constructor url, Call call, StringLiteral src
// where url.getDeclaringType().hasQualifiedName("java.net","URL") and
//     call.getCallee() = url and
//     DataFlow::localFlow(DataFlow::exprNode(src), DataFlow::exprNode(call.getArgument(0)))
// select src


// 2: Write a query that finds all hard-coded strings used to create a java.net.URL, using global data flow
// module StringToURLFlowConfiguration implements DataFlow::ConfigSig {
//     predicate isSource(DataFlow::Node source) {
//       exists( StringLiteral src |
//             source.asExpr() = src
//         )
//     }
  
//     predicate isSink(DataFlow::Node sink) {
//       exists(Call call |
//             sink.asExpr() = call.getArgument(0) and
//             call.getCallee().(Constructor).getDeclaringType().hasQualifiedName("java.net","URL")
//         )
//     }
//   }
  
//   module StringToURLFlow = DataFlow::Global<StringToURLFlowConfiguration>;

//   from DataFlow::Node src, DataFlow::Node sink
//   where StringToURLFlow::flow(src, sink)
//   select src, "This string constructs a URL $@.", sink, "here"


// 3: Write a class that represents flow sources from java.lang.System.getenv(..)
// class GetEnvSource extends MethodCall{
//     GetEnvSource(){
//         exists(Method m | m = this.getMethod() |
//             m.hasName("getenv") and
//             m.getDeclaringType() instanceof TypeSystem
//         ) 
//     }
//     Parameter getAnUntrustedParameter(){
//         result = this.getMethod().getParameter(0)
//     }
// }



// 4: Using the answers from 2 and 3, write a query which finds all global data flows from getenv to java.net.URL
// module GetEnvToURLConfiguration implements DataFlow::ConfigSig {
//     predicate isSource(DataFlow::Node source) {
//         exists(GetEnvSource getenv |
//             source.asParameter() = getenv.getAnUntrustedParameter()
//         )
//     }
  
//     predicate isSink(DataFlow::Node sink) {
//         exists(Call call |
//             sink.asExpr() = call.getArgument(0) and
//             call.getCallee().(Constructor).getDeclaringType().hasQualifiedName("java.net","URL")
//         )
//     }
//   }
  
//   module GetEnvFlow = DataFlow::Global<GetEnvToURLConfiguration>;

//   from DataFlow::Node source, DataFlow::Node sink
//   where GetEnvFlow::flow(source, sink)
//   select  source, "This environment variable constructs a URL $@.", sink, "here"


