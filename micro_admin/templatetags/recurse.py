from django import template

register = template.Library()

class RecurseNode(template.Node):
    def __init__(self, var, name, child, node_list):
        self.var = var
        self.name = name
        self.child = child
        self.node_list = node_list

    def __repr__(self):
        return '<RecurseNode>'

    def render_callback(self, context, vals, level):
        output = []
        try:
            if not isinstance(vals, (list, tuple)):
                vals = [vals]
        except:
            vals = [vals]
        
        if vals:
            if 'loop' in self.node_list:
                output.append(self.node_list['loop'].render(context))
            
            for val in vals:
                context.push()
                context['level'] = level
                context[self.name] = val
                
                if 'child' in self.node_list:
                    output.append(self.node_list['child'].render(context))
                    child = self.child.resolve(context)
                    if child:
                        output.append(self.render_callback(context, child, level + 1))
                
                if 'endloop' in self.node_list:
                    output.append(self.node_list['endloop'].render(context))
                else:
                    output.append(self.node_list['endrecurse'].render(context))
                
                context.pop()
            
            if 'endloop' in self.node_list:
                output.append(self.node_list['endrecurse'].render(context))
        
        return ''.join(output)

    def render(self, context):
        vals = self.var.resolve(context)
        return self.render_callback(context, vals, 1)

def do_recurse(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 6 or bits[2] != 'with' or bits[4] != 'as':
        raise template.TemplateSyntaxError(
            "Invalid syntax for 'recurse' tag. Usage: {% recurse [var] with [child] as [name] %}"
        )
    
    child = parser.compile_filter(bits[1])
    var = parser.compile_filter(bits[3])
    name = bits[5]

    node_list = {}
    while len(node_list) < 4:
        temp = parser.parse(('child', 'loop', 'endloop', 'endrecurse'))
        tag = parser.tokens[0].contents
        node_list[tag] = temp
        parser.delete_first_token()
        if tag == 'endrecurse':
            break

    return RecurseNode(var, name, child, node_list)

register.tag('recurse', do_recurse)
